(function(document, window) {
window.ui=window.ui||{};
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
})(document, window);