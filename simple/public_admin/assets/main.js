(function(document, window) {
window.ui=window.ui||{};
let pending_refresh=false;
async function refresh() {
    if (pending_refresh) return;
    const by = document.getElementById("top_by");
    const by_key = by.value;
    const el = document.getElementById("top_out");
    const t1=Date.now();
    let res;
    try {
        res = await xrpc_call("_admin.get_stats");
    } catch(e) {
        res = null;
    }
    if (res) {
        const items=Object.entries(res[by_key]).toSorted((a, b)=>b[1]-a[1]);
        const out = items.map(([n,c])=>`${n}\t${c}`).join("\n")
        el.innerText = out
    }
    const ev = document.getElementById("top_every");
    setTimeout(refresh, ev.value);
}
ui.refresh=async function() {
    refresh();
}
setTimeout(refresh, 1000);
})(document, window);