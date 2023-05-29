package main

import (
	"bufio"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	b64 "encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type count32 int32

func (c *count32) inc() int32 {
	return atomic.AddInt32((*int32)(c), 1)
}

func (c *count32) get() int32 {
	return atomic.LoadInt32((*int32)(c))
}

var lock = &sync.RWMutex{}

// type alias for convenience
type mapStr2Any = map[string]interface{}

type StdioApp struct {
	methods    mapStr2Any
	methods_ch map[string](chan interface{})
	id2id      map[string]string
	writer     *bufio.Writer
	logger     *bufio.Writer
	suffix     string
	counter    count32
}

var stdioAppInstance *StdioApp

// TODO: when handling error
// see https://stackoverflow.com/a/66380482/810282
var errorInterface = reflect.TypeOf((*error)(nil)).Elem()

func coded_err_from_str(s string) *CodedError {
	codename, msg, found := strings.Cut(s, ":")
	if !found {
		codename = "error"
		msg = s
	}
	err := CodedError{codename: codename, msg: msg}
	return &err
}

func to_coded_error(a interface{}) *CodedError {
	k := reflect.ValueOf(a).Kind()
	t := reflect.TypeOf(a)
	if k == reflect.Ptr {
		if !t.Implements(errorInterface) {
			return nil
		}
		n := reflect.Indirect(reflect.ValueOf(a)).Type().Name()
		s := a.(error).Error()
		if n == "errorString" || n == "error" {
			return coded_err_from_str(s)
		}
		err := CodedError{codename: n, msg: s}
		return &err
	}
	coded, is_coded := a.(CodedError)
	if is_coded {
		return &coded
	}
	// TODO: consider errors.Is() or errors.As() to unwrap CodedError
	e, is_err := a.(error)
	if !is_err {
		return nil
	}
	s := e.Error()
	return coded_err_from_str(s)
}

func (app *StdioApp) out(out interface{}) {
	msg_b, err := json.Marshal(out)
	if err != nil {
		msg_b = []byte(err.Error())
		lock.Lock()
		app.writer.Write(msg_b)
		app.writer.WriteByte('\n')
		// app.writer.Flush()
		lock.Unlock()
	}
	lock.Lock()
	app.writer.Write(msg_b)
	app.writer.WriteByte('\n')
	app.writer.Flush()
	lock.Unlock()

}

func (app *StdioApp) log(out interface{}) {
	msg_b, _ := json.Marshal(out)
	app.logger.Write(msg_b)
	app.logger.WriteByte('\n')
	app.logger.Flush()
}

func (app *StdioApp) recover_panic(id string) {
	if r := recover(); r != nil {
		coded_err := to_coded_error(r)
		if coded_err == nil {
			coded_err = coded_err_from_str(fmt.Sprint(r))
		}
		app.out(map[string]interface{}{
			"id": id,
			"error": map[string]interface{}{
				"codename": coded_err.codename,
				"message":  coded_err.msg,
			},
		})
	}
}

func (app *StdioApp) add_method(name string, f interface{}) {
	fv := reflect.ValueOf(f)
	in_count := fv.Type().NumIn()
	out_count := fv.Type().NumOut()
	if 2 != in_count {
		// err := errors.New("The number of params is out of index.")
		panic("bad method sigature: input count should be 2")
	}
	if 1 != out_count {
		panic("bad method sigature: output count should be 1")
	}
	app.methods[name] = func(in_ []reflect.Value) {
		id := in_[0].String()
		defer app.recover_panic(id)
		ret := fv.Call(in_)
		lock.Lock()
		delete(app.methods_ch, id)
		lock.Unlock()
		ret0 := ret[0]
		ret_i := ret0.Interface()
		// ret_err, is_err := ret_i.(error)
		coded_err := to_coded_error(ret_i)
		if coded_err != nil {
			app.out(map[string]interface{}{
				"id": id,
				"error": map[string]interface{}{
					"codename": coded_err.codename,
					"message":  coded_err.msg,
				},
			})
		} else {
			ret := map[string]interface{}{
				"id":     id,
				"result": ret_i,
			}
			app.out(ret)
		}
	}
}

func (app *StdioApp) call(name string, params mapStr2Any, id string) {
	pos := strings.LastIndexByte(name, '.')
	var n string
	if pos < 0 {
		n = name
	} else {
		n = name[pos+1:]
	}
	m := app.methods[n]
	if m == nil {
		app.out(map[string]interface{}{
			"id": id,
			"error": map[string]interface{}{
				"codename": "bad-method-name",
				"message":  "method not found",
			},
		})
		return
	}
	f := reflect.ValueOf(m)
	ch := make(chan interface{})
	lock.Lock()
	app.methods_ch[id] = ch
	lock.Unlock()
	in := make([]reflect.Value, 2)
	in[0] = reflect.ValueOf(id)
	in[1] = reflect.ValueOf(params)
	in_ := make([]reflect.Value, 1)
	in_[0] = reflect.ValueOf(in)
	// TODO: move logic to add_method
	go f.Call(in_)
}

func (app *StdioApp) invoke(id string, method string, params mapStr2Any) (interface{}, error) {
	lock.RLock()
	ch := app.methods_ch[id]
	lock.RUnlock()
	inv_id := strconv.Itoa(int(app.counter.inc())) + app.suffix
	lock.Lock()
	app.id2id[inv_id] = id
	lock.Unlock()
	msg := mapStr2Any{
		"id":     inv_id,
		"method": method,
		"params": params,
	}
	app.out(msg)
	ret := <-ch
	ret_err, err_found := ret.(CodedError)
	if err_found {
		return nil, &ret_err
	}
	lock.Lock()
	delete(app.id2id, inv_id)
	lock.Unlock()
	return ret, nil
}

func (app *StdioApp) readline(ch chan map[string]interface{}) {
	reader := bufio.NewReader(os.Stdin)
	for true {
		line, err := reader.ReadString('\n')
		if err != nil {
			log.Fatal(err)
		}
		// fmt.Println("Received: ", line)
		var parsed interface{}
		// TODO: try to avoid converting string to []byte by using ReadBytes('\n')
		err2 := json.Unmarshal([]byte(line), &parsed)
		if err2 != nil {
			continue
		}
		parsed_map, ok := parsed.(map[string]interface{})
		if !ok {
			continue
		}
		ch <- parsed_map
	}
}

type CodedError struct {
	codename string // error occurred after reading Offset bytes
	msg      string // description of error
}

func (e *CodedError) Error() string { return e.msg }

type CustomError struct {
	codename string // error occurred after reading Offset bytes
	msg      string // description of error
}

func (e *CustomError) Error() string { return e.msg }

func (app *StdioApp) loop() {
	ch := make(chan mapStr2Any)
	go app.readline(ch)
	for true {
		parsed := <-ch
		id, _ := parsed["id"].(string)
		method, method_found := parsed["method"].(string)
		if method_found {
			params, _ := parsed["params"].(mapStr2Any)
			app.call(method, params, id)
			continue
		}
		lock.RLock()
		id2, id2found := app.id2id[id]
		lock.RUnlock()
		if !id2found {
			continue
		}
		res_ch, _ := app.methods_ch[id2]
		if res_ch == nil {
			continue
		}

		err, err_found := parsed["error"].(mapStr2Any)
		if err_found {
			err_code, _ := err["codename"].(string)
			err_msg, _ := err["message"].(string)
			e := CodedError{codename: err_code, msg: err_msg}
			res_ch <- e
			continue
		}
		res_ch <- parsed["result"]
	}
}

func getSalt(n int) []byte {
	nonce := make([]byte, n)
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		panic(err.Error())
	}
	return (nonce)
}

func (app *StdioApp) _init() {
	app.methods = make(mapStr2Any)
	app.methods_ch = make(map[string](chan interface{}))
	app.id2id = make(map[string]string)
	app.writer = bufio.NewWriter(os.Stdout)
	app.logger = bufio.NewWriter(os.Stderr)
	now := time.Now().UnixMicro()
	pid := os.Getpid()
	rnd := getSalt(21)
	hash := hmac.New(sha256.New, rnd)
	hash.Write([]byte(strconv.Itoa(pid) + "@" + strconv.FormatInt(now, 10)))
	app.suffix = "." + string(b64.URLEncoding.EncodeToString(hash.Sum(nil)))
}

func getStdioAppInstance() *StdioApp {
	if stdioAppInstance == nil {
		lock.Lock()
		defer lock.Unlock()
		if stdioAppInstance == nil {
			fmt.Println("Creating single instance now.")
			stdioAppInstance = &StdioApp{}
			stdioAppInstance._init()
		} else {
			fmt.Println("Single instance already created.")
		}
	} else {
		fmt.Println("Single instance already created.")
	}

	return stdioAppInstance
}
