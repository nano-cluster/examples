
function getRndSuffix(len) {
    let ret="";
    for(let i=0;i<len;++i) {
      ret+=parseInt(Math.random()*16).toString(16);
    }
    return ret;
}

async function xrpc_call_http(method, params={}, id=null, extended=true) {
    const url = (extended)?`/xrpc/${method}`:'/xrpc';
    const body = {"method": method, "params": params || {}};
    if (extended) {
        delete body.method;
    }
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    let parsed;
    if (!res.ok) {
        if (res.headers.get("content-type")=="application/json") {
            const text = await res.text();
            parsed = JSON.parse(text);
            const err = new Error(parsed.error.message);
            err.codename = parsed.error.codename;
            err.validations = parsed.error.validations;
            throw err;
        }
        throw new Error("req failed");
    }
    try {
        const text = await res.text();
        parsed = JSON.parse(text);
    } catch (e) {
        throw new Error("req failed");
    }
    if (parsed.error) {
        const err = new Error(parsed.error.message);
        err.codename = parsed.error.codename;
        throw err;
    }
    return parsed.result;
}

async function xrpc_call_ws(method, params={}) {
    if (!window.rpc_ws) return;
    ++rpc_ws.counter;
    let id = (rpc_ws.counter).toString()+"."+rpc_ws.sfx;
    let req = {"method": method, "params": params, "id": id};
    rpc_ws.socket.send(JSON.stringify(req));
    return new Promise(function(resolve, reject){
        rpc_ws.cbs_by_id[id] = [resolve, reject];
    });
}

function xrpc_call(method, params={}) {
    if (window.rpc_ws && rpc_ws.ready) return xrpc_call_ws(method, params);
    return xrpc_call_http(method, params);
}

function rpc_ws_notify(method, params) {
    if (!window.rpc_ws) return;
    let req = {"method": method, "params": params};
    rpc_ws.socket.send(JSON.stringify(req));
}

(function(document, window) {
window.rpc_ws = window.rpc_ws || {}
const rpc_ws = window.rpc_ws
rpc_ws.cbs_by_id = rpc_ws.cbs_by_id || {};
rpc_ws.sfx = getRndSuffix(32);
rpc_ws.counter = 0;
const ws_url = (document.location.protocol=='http:'?'ws:':'wss:')+`//${document.location.host}/ws`;
let socket = new WebSocket(ws_url);
socket.addEventListener('open', function (event) {
    rpc_ws.socket = socket;
    rpc_ws.ready = true;
    console.log("socket ready");
});
socket.addEventListener("close", function(event) {rpc_ws.ready = false;console.log("socket closed");});
socket.addEventListener("error", function(event) {rpc_ws.ready = false;console.log("socket error");});
socket.addEventListener('message', function (event) {
    // NOTE: can be handled like this: await event.data.text()
    // NOTE: binary can be handled too: await event.data.arrayBuffer()
    if (typeof event.data!="string") return;
    const message = event.data;
    let parsed;
    try {
        parsed = JSON.parse(message);
    } catch(e) {
        return;
    }
    const id = parsed.id;
    if (!id) return;
    const callbacks = rpc_ws.cbs_by_id[id];
    if (!callbacks) return;
    delete rpc_ws.cbs_by_id[id];
    const [resolve, reject] = callbacks;
    if (parsed.error) {
        const err = new Error(parsed.error.message);
        err.code = parsed.error.code;
        err.validations = parsed.error.validations;
        return reject(err);
    }
    resolve(parsed.result);
});
})(document, window);