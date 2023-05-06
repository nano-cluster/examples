export class App {
    constructor() {
        this._methods = {};
    }
    add_method(name, callback) {
        this._methods[name] = callback
    }
    async call(parsed) {
        let {method, params} = parsed;
        if (method.indexOf(".")>=0) {
            const parts = method.split(".");
            method = parts[parts.length-1];
        }
        if (!params) params={};
        return this._methods[method](params);
    }
}
