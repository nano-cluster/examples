<?php

function get_rnd() {
    $t = (int)(microtime(1)*1000);
    $data = uniqid('', true);
    return str_replace(['=', '+', '/'], ['', '-', '_'], base64_encode(hash_hmac('sha256', $data, getmypid().".".$t, 1)));
}

function get_next_id() {
    global $suffix, $counter;
    ++$counter;
    return $counter.".".$suffix;
}


$suffix = get_rnd();
$counter = 0;


/**
 * using fibers
 * https://www.php.net/manual/en/language.fibers.php
 */
class StdIOApp {
    protected static $_methods = [];
    protected static $tasks = [];
    protected static $invokes = [];
    protected static $_ids = []; // mapping between fiber-object id and request id

    protected function __construct(){

    }
    public static function log($line) {
        if (!is_string($line)) {
            $line=json_encode($line, JSON_UNESCAPED_UNICODE);
        }
        fwrite(STDERR, $line);
        fwrite(STDERR, "\n");
    }

    public static function loop() {
        while(true) {
            static::read(null);
            static::task_loop();
        }
    }

    public static function read($wait=0) {
        // var_dump("wait", $wait, static::$invokes);
        $r=[STDIN];
        $w=[];
        $e=[STDIN];
        $i=stream_select($r, $w, $e, $wait);
        if (!empty($e)) {
            fwrite(STDERR, "EXCEPTION\n");
            exit(1);
        }
        if (empty($r)) return;
        $line = fgets(STDIN);
        if (empty($line)) return;
        $parsed = json_decode($line);
        static::handle_one(null, $parsed);
    }

    public static function task_loop() {
        while(count(static::$tasks)) {
            // TODO: consider replace this with channel parallel\Channel
            [$fiber, $parsed] = array_shift(static::$tasks);
            $fiber = static::handle_one($fiber, $parsed);
            if ($fiber && $fiber->isTerminated()) {
                $fid = spl_object_id($fiber);
                $id = static::$_ids[$fid];
                unset(static::$_ids[$fid]);
                // TODO: handle error, this throws FiberError $e->previous with the actual error
                try {
                    $res = $fiber->getReturn();
                } catch(FiberError $e) {
                    $p = $e->getPrevious();
                    var_dump($e->getMessage(), $p?$p->getMessage():null);
                    echo (string)($e), $e->getTraceAsString()."\n";
                    $res = null;
                }
                echo json_encode(['id'=>$id, 'result'=>$res], JSON_UNESCAPED_UNICODE)."\n";
            }
            static::read(0);
        }
    }
    public static function add_class($class_name) {
        $ref_class = new ReflectionClass($class_name);
        $methods = $ref_class->getMethods(ReflectionMethod::IS_STATIC | ReflectionMethod::IS_PUBLIC);
        foreach($methods as $method) {
            // TODO: strip action_
            $name = $method->name;
            $prefix = substr($name, 0, 7);
            if ($prefix!="action_") continue;
            $name = substr($name, 7);
            $cb = function($params)use($method) {
                if ($params instanceof stdClass) {
                    $params = get_object_vars($params);
                }
                $ret=null;
                try {
                    $ret = $method->invokeArgs(null, $params);
                } catch(Throwable $e) {
                    $ret = $e;
                } finally {
                    StdIOApp::invoke("no_op");
                }
                return $ret;
            };
            static::$_methods[$name] = [$method, $cb];
            /*
            var_dump($method->name);
            var_dump($method->hasPrototype());
            var_dump($method->getDocComment()); // returns false
            $params = $method->getParameters();
            foreach($params as $param) {
                var_dump($param->name);
                var_dump($param->getDefaultValue());
                var_dump($param->isDefaultValueAvailable());
                var_dump($param->isDefaultValueConstant());
                var_dump($param->isOptional());
                $type = $param->getType();
                if ($type) {
                    var_dump((string)$type);
                    var_dump($type->getName());
                    var_dump($type->isBuiltin());
                    var_dump($type->allowsNull());
                }
            }
            */
        }
        
    }


    public static function call($method_name, $params, $id) {
        $ls = explode(".", $method_name);
        $method_name = $ls[count($ls)-1];
        list($method, $cb) = static::$_methods[$method_name]??[null, null];
        if (!$method) {
            throw new Exception("method not found");
        }
        // https://www.php.net/manual/en/class.fiber.php
        $fiber = new Fiber($cb);
        static::$_ids[spl_object_id($fiber)] = $id;
        $fiber->start($params);
        return $fiber;
    }

    public static function __callStatic($name, $arguments)
    {
        if (substr($name, 0, 7)!="invoke_") {
            throw new Exception("method $name not found");
        }
        $method_name = str_replace('__', '.', substr($name, 7));
        static::log([$method_name, $arguments]);
        return static::invoke($method_name, $arguments[0]);
    }

    public static function invoke($method, $params=[], $id="") {
        if (!$id) {
            $id=get_next_id();
        }
        $parsed = (object)['id'=>$id, 'method'=>$method, 'params'=>$params];
        static::$tasks[] = [Fiber::getCurrent(), $parsed];
        return Fiber::suspend();
    }

    public static function handle_one($fiber, $parsed) {
        $id = $parsed->id??null;
        if (!$id) {
            $id = get_next_id();
        }
        $method = $parsed->method??null;
        if ($fiber) {
            if ($method=="no_op") {
                if (!$fiber->isTerminated() && $fiber->isSuspended()) {
                    try {
                        $fiber->resume(null);
                    }catch(Throwable $e) {
                    }
                }
                return $fiber;
            }
            if ($id) static::$invokes[$id] = $fiber;
            echo json_encode($parsed, JSON_UNESCAPED_UNICODE)."\n";
            return $fiber;
        }
        if ($method) {
            $fiber = static::call($method, $parsed->params??[], $id);
            return $fiber;
        }
        if (!isset(static::$invokes[$id])) {
            return;
        }
        $fiber = static::$invokes[$id];
        unset(static::$invokes[$id]);
        if (!$fiber) return;
        if (!empty($parsed->error)) {
            $fiber->throw(new Exception($parsed->error->message));
            return $fiber;
        }
        if (!$fiber->isTerminated() && $fiber->isSuspended()) {
            try {
                $fiber->resume($parsed->result??null);
            } catch(Throwable $e) {
            }
        }
        return $fiber;
    }

}
