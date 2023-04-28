import {JsonRpcClient} from "./json_rpc_ws.js"

const range = n => [...Array(n).keys()]

async function main() {
  const json_rpc = new JsonRpcClient();
  await json_rpc.connect('ws://localhost:3000/ws');
  const values = range(1000);
  
  await json_rpc.call("mycalc.sqsum", {values}).then(console.log)
  
  
  var t1=Date.now();
  var promises=[];
  const n=2000;
  for(let i=0;i<n;++i) {
    promises.push(json_rpc.call("mycalc.sqsum", {values}).then(({sum, sqsum})=>sum*sum-sqsum));
  }
  var t2=Date.now();
  await Promise.all(promises);
  var t3=Date.now();
  console.log("time to send the 2k requests: ", t2-t1, (t2-t1)/n);
  console.log("time to get responses: ", t3-t2, (t3-t2)/n);
  console.log("total time: ", t3-t1, (t3-t1)/n);
  process.exit(0);
}

main();
