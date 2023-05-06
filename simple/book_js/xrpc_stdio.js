// consider using rl
// import * as readline from 'node:readline/promises';
// import {stdin, stdout} from 'process';

import * as fs from 'node:fs';

import crypto from 'crypto';



// taken from @alsadi/async_utils

/**
 * await the returned promise to sleep the given time
 *
 * @param {number} ms number of millisecond
 * @returns {Promise} a promise that fulfilled after the given time
 */
export function sleep(ms) {
    // eslint-disable-next-line promise/avoid-new
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * convert events comming from an emitter into into async generator
 * used like this
 * for await ([event_name, item_args] of generatorFromEvents(ev, ['event1'], ['close'], ['error']) {}
 *
 * @param {EventEmitter} emitter - the event emitter to be converted to generator
 * @param {Array<string>} itemEvents - list of item event names
 * @param {Array<string>} exitEvents - list of exit event names
 * @param {Array<string>} errorEvents - list of error event names
 * @param {boolean} includeExitItem - should include the exit event in items
 * @yields {Array} - yields [event_name, event_args]
 */
export async function* generatorFromEvents(
    emitter,
    itemEvents,
    exitEvents = null,
    errorEvents = null,
    includeExitItem = false
) {
    const items = [];
    let item_resolve;
    let item_promise = new Promise((resolve) => (item_resolve = resolve));
    let exit_resolve;
    const exit_promise = new Promise((resolve) => (exit_resolve = resolve));
    let error_resolve;
    const error_promise = new Promise((resolve) => (error_resolve = resolve));

    /**
     * internal function
     *
     * @param {*} arg - item
     */
    function cb_item(arg) {
        items.push(arg);
        item_resolve(arg);
        item_promise.done = true;
        item_promise = new Promise((resolve) => (item_resolve = resolve));
    }
    /**
     * internal function
     *
     * @param {*} arg - item
     */
    function cb_exit(arg) {
        exit_resolve(arg);
        exit_promise.done = true;
    }
    /**
     * internal function
     *
     * @param {*} arg - item
     */
    function cb_error(arg) {
        error_resolve(arg);
        error_promise.done = true;
    }
    for (const name of itemEvents) {
        emitter.on(name, (...args) => cb_item([name, args]));
    }
    for (const name of exitEvents) {
        emitter.on(name, (...args) => cb_exit([name, args]));
    }
    for (const name of errorEvents) {
        emitter.on(name, (...args) => cb_error([name, args]));
    }
    let has_more = true;
    while (has_more) {
        await Promise.race([item_promise, exit_promise, error_promise]);
        while (items.length) {
            yield items.shift();
        }
        if (error_promise.done) {
            const [name, args] = await error_promise;
            has_more = false;
            if (
                args &&
                args.length &&
                args.length >= 1 &&
                args[0] instanceof Error
            ) {
                const error = args[0];
                error.event_name = name;
                throw error;
            }
            const error = new Error("error event");
            error.event_name = name;
            error.event_args = args;
            throw error;
        }
        if (exit_promise.done) {
            const item = await exit_promise;
            has_more = false;
            if (includeExitItem) yield item;
            break;
        }
    }
}

async function *asyncGenMap(gen, item_mapper) {
    for await(const item of gen) {
        for await(const mapped of item_mapper(item)) {
            yield mapped;
        }
    }
}


export class StdIOApp {
    constructor(app) {
        this.app = app;
        this._id = this.get_random();
        this._counter = 0;
        this._invokes = {};
    }

    log(s) {
        fs.writeSync(2, `${s}\n`)
    }

    get_random() {
        const hmac = crypto.createHmac("sha256", Date.now().toString()+"@"+process.pid.toString());
        const rnds8Pool = new Uint8Array(256);
        crypto.randomFillSync(rnds8Pool);
        hmac.update(rnds8Pool);
        return hmac.digest('base64').replaceAll('=', '').replaceAll('+', '-').replaceAll('/', '_');
    }
    

    invoke(method, params, id="") {
        const self=this;
        ++self._counter;
        if (id=="") {
            id=self._counter.toString()+"."+self._id;
        }
        if (!params) params={};
        return new Promise(function(resolve, reject) {
            self._invokes[id]=[resolve, reject];
            fs.writeSync(1, JSON.stringify({id, method, params})+"\n")
        });
    }

    async handle_one(parsed) {
        const id = parsed.id;
        const method = parsed.method;
        if (method) {
            this.app.call(parsed).then((r)=>({id: id, result: r})).catch((e)=>({error:{message:e.message}})).then(function(ret){
                fs.writeSync(1, JSON.stringify(ret)+ "\n");
            });
        } else {
            if (!id) return;
            const [resolve, reject] = this._invokes[id];
            if (parsed.error) {
                err = new Error(parsed.error.message)
                return reject(err);
            }
            return resolve(parsed.result);
        }
    }

    async loop() {
        process.stdin.resume();
        process.stdin.setEncoding('utf8');
        const gen = generatorFromEvents(process.stdin, ["data"], ["end"], ["error"], false)
        const line_gen = asyncGenMap(gen, async function*([event, [data]]){
            for(const item of data.split("\n")) {
                yield item;
            }
        })
        for await(const item of line_gen) {
            if (!item || item=="") continue;
            const parsed = JSON.parse(item)
            await this.handle_one(parsed);
        }
    }
}