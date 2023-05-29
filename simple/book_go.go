package main

import (
	"errors"
	"math"
)

var stdioApp = getStdioAppInstance()

var ValidationError = errors.New("Validation Error")

func action_list(id string, params mapStr2Any) interface{} {
	page_f, _ := params["page"].(float64)
	per_page_f, _ := params["per_page"].(float64)
	page := int(page_f)
	if page <= 0 {
		page = 1
	}
	if per_page_f <= 0 {
		per_page_f = 10
		// panic("something: bad value for page")
		// panic(ValidationError)
		// return os.ErrNotExist
		// return &CodedError{codename: "validation-error", msg: "per_page must be greater than zero"}
		// panic(&CodedError{codename: "validation-error", msg: "per_page must be greater than zero"})
	}
	per_page := int(per_page_f)
	stdioApp.log(mapStr2Any{"got": mapStr2Any{"page": page, "per_page": per_page}})
	count_ret, _ := stdioApp.invoke(id, "db.fetch_one", mapStr2Any{"sql": "select count(*) from books"})
	count_res, _ := count_ret.(mapStr2Any)
	count_item, _ := count_res["item"].([]interface{})
	count := count_item[0].(float64)
	stdioApp.log(count)
	offset := (page - 1) * per_page
	meta := mapStr2Any{"count": count, "pages": math.Ceil(count / per_page_f)}
	query_ret, _ := stdioApp.invoke(id, "db.fetch_all", mapStr2Any{
		"sql":    "select * from books limit :per_page offset :offset",
		"params": mapStr2Any{"offset": offset, "per_page": per_page},
		"kv":     1,
	})
	query_res, _ := query_ret.(mapStr2Any)
	query_items, _ := query_res["items"].([]interface{})
	return mapStr2Any{"meta": meta, "items": query_items}
}

func main() {
	stdioApp.add_method("list", action_list)
	stdioApp.loop()

}
