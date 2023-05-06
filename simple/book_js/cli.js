import {App} from "./xrpc.js"
import {StdIOApp} from "./xrpc_stdio.js"

const app = new App();
const stdio_app = new StdIOApp(app);
app.add_method("list", async function({page, per_page}) {
    if (!page) page=1;
    if (!per_page) per_page=10;
    page = parseInt(page);
    const {item: count} = await stdio_app.invoke("db.fetch_one", {
        "sql":"select count(*) c from books",
    });
    stdio_app.log('got count = '+count);
    // const meta = {};
    const pages = Math.ceil(count/per_page);
    const meta = {count, pages};
    const offset = (page-1)*per_page;
    const items = await stdio_app.invoke("db.fetch_all", {
        "sql":"select * from books limit 10 offset :offset",
        "params": {"offset": offset}
    });
    return {meta, items}
});

export async function main() {
    await stdio_app.loop();
}