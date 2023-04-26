(function(document, window) {
window.ui=window.ui||{};
ui.ping_click=async function() {
    const el = document.getElementById("res_ping");
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
    const res = await xrpc_call("book.book_search", {q:"foo"});
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
ui.btn4_click=async function() {
    const el = document.getElementById("res4");
    const t1=Date.now();
    let res;
    try {
        res = await xrpc_call("_admin.get_stats", {});
    } catch(e) {
        res = {message: e.message, codename: e.codename}
    }
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res);
}
})(document, window);