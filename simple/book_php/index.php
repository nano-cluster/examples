<?php
require_once("./xrpc.php");

class Book {
    /**
     * get list of books
     */
    public static function action_delme(int $page=1, ?int $per_page=10) {
        return ['meta'=>['count'=>0, 'pages'=>0], 'items'=>[]];
    }

    /**
     * get list of books
     */
    public static function action_list(int $page=1, ?int $per_page=10) {
        if ($per_page<=0) $per_page=10;
        $res = StdIOApp::invoke_db__fetch_one(['sql'=>'select count(*) from books']);
        $count = $res->item[0];
        $offset = ($page-1)*$per_page;
        $res = StdIOApp::invoke_db__fetch_all([
            'sql'=>'select * from books limit :per_page offset :offset',
            'params'=>['offset'=>$offset, 'per_page'=>$per_page],
            'kv'=>1,
        ]);
        $meta = ['count'=>$count, 'pages'=>ceil($count/$per_page)];
        throw new Exception("too many monkeys");
        return [
            'meta'=>$meta,
            'items'=>$res->items,
        ];
    }
}

StdIOApp::add_class(Book::class);
StdIOApp::loop();