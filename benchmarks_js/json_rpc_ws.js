import WebSocket from 'ws';

export class JsonRpcClient {
    constructor() {
        this.sfx = this.getRndSuffix(32);
    }
    getRndSuffix(len) {
        let ret="";
        for(let i=0;i<len;++i) {
          ret+=parseInt(Math.random()*16).toString(16);
        }
        return ret;
    }
    connect(url) {
        let self = this;
        this.cbs_by_id = {};
        this.counter = 0;
        this.url = url;
        let ws = new WebSocket(url);
        this.ws = ws;
        return new Promise(function(resolve){
            ws.on('open', function() {
                resolve(ws);
            });
            ws.on('message', (data, isBinary)=>self.on_message(isBinary ? data : data.toString()));
        });
    }
    on_message(message) {
        const parsed = JSON.parse(message);
        const id = parsed.id;
        const callbacks = this.cbs_by_id[id];
        if (!callbacks) return;
        delete this.cbs_by_id[id];
        const [resolve, reject] = callbacks;
        if (parsed.error) {
            const err = new Error(parsed.error.message);
            err.code = parsed.error;
            return reject(err);
        }
        resolve(parsed.result);
    }
    call(method, params) {
        let self = this;
        ++this.counter;
        let id = (this.counter).toString()+"."+this.sfx;
        let req = {"method": method, "params": params, "id": id};
        this.ws.send(JSON.stringify(req));
        return new Promise(function(resolve, reject){
            self.cbs_by_id[id] = [resolve, reject];
        });
    }
}

export class JsonRpcServer {
    constructor() {
        this.methods = {};
    }
    send_err(ws, code, message, id) {
        const json_rpc_res = {"jsonrpc": "2.0", "error": {code, message}, "id": id};
        ws.send(JSON.stringify(json_rpc_res));
    }
    add_method(method_name, cb) {
        this.methods[method_name] = cb;
    }
    listen(port) {
        let self = this;
        const wss = new WebSocket.Server({
            port: port,
        });
        wss.on('connection', function(ws) {
            console.log("got connection")
            ws.on('message', async function(message) {
                // console.log('received:', message);
                const parsed = JSON.parse(message);
                const {method, params, id} = parsed;
                if (typeof method!="string") {
                    return self.send_err(ws, "400-bad-method", "bad method", id);
                }
                if (typeof id!="string" && typeof id!="number") {
                    return self.send_err(ws, "400-bad-id", "bad id", id);
                }
                const method_cb = self.methods[method];
                if (!method_cb) {
                    return self.send_err(ws, "404", "method not found", id);
                }
                let res;
                try {
                    res = await method_cb(params);
                } catch(e) {
                    return self.send_err(ws, e.code, e.message, id);
                }
                const json_rpc_res = {"jsonrpc": "2.0", "result": res, "id": id};
                ws.send(JSON.stringify(json_rpc_res));
            });
        });
    }
    
}

