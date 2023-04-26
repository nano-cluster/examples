(function(document, window) {
window.ui=window.ui||{};
ui.btn1_click=async function() {
    const el = document.getElementById("res1");
    const t1=Date.now();
    const res = await xrpc_call("_admin.get_stats");
    const dt=Date.now()-t1;
    el.innerText = `${dt} ms: `+JSON.stringify(res, null, 2);
}
})(document, window);