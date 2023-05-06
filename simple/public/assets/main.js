(function(document, window) {
window.ui=window.ui||{};
ui.ping_click=async function(t) {
    const dst_id=t.getAttribute("data-dst");
    const el = document.getElementById(dst_id);
    const t1=Date.now();
    const res = await xrpc_call("_ping");
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
ui.btn1_click=async function() {
    const el = document.getElementById("res1");
    const t1=Date.now();
    const res = await xrpc_call("mycalc.rnd_num");
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
ui.btn2_click=async function() {
    const el = document.getElementById("res2");
    const t1=Date.now();
    const res = await xrpc_call("mycalc.num_add", {a:10, b:20});
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
ui.btn3_click=async function() {
    const el = document.getElementById("res3");
    const t1=Date.now();
    const res = await xrpc_call("book.list", {page: 1});
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
ui.btn4_click=async function() {
    const el = document.getElementById("res4");
    const t1=Date.now();
    let res;
    try {
        res = await xrpc_call("book_js.list", {});
    } catch(e) {
        res = {message: e.message, codename: e.codename}
    }
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
})(document, window);