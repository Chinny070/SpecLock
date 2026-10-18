// Candidate-specific API and agent negative regressions. Signers are ephemeral,
// live only in this process, and no signing material is serialized.
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';
import { writeFile } from 'node:fs/promises';
import { createAccount, createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';
const CONTRACT='0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14', AMOUNT=100_000_000_000_000n;
const buyer=createAccount(), provider=createAccount(), client=createClient({chain:studionet}), entries=[];
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function clean(x){return JSON.parse(JSON.stringify(x,(_k,v)=>typeof v==='bigint'?v.toString():v));}
function execResult(r){const x=r.consensus_data?.leader_receipt;return Array.isArray(x)?x.find(v=>v.mode==='leader')?.execution_result:x?.execution_result??null;}
function brief(r,value=0n){return {hash:r.hash??r.tx_id,status:r.statusName??r.status_name??null,result_name:r.result_name??null,execution_result:execResult(r),value_credited:r.value_credited??null,value_sent:String(value),votes:r.consensus_data?.votes??null};}
const path='docs/evidence/studionet-negative-regressions-2026-10-18.json';
async function save(){await writeFile(path,JSON.stringify({network:'GenLayer Studio Network',chainId:61999,contract:CONTRACT,sourceCommit:'b6fdb8a6e02b93acaa6d2dc942bf04b9edff96df',sourceSha256:'0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE',actors:{buyer:buyer.address,provider:provider.address},entries},null,2)+'\n');}
async function wait(hash,value=0n){let last;for(let i=0;i<180;i++){try{const r=await client.waitForTransactionReceipt({hash,status:TransactionStatus.FINALIZED,interval:5000,retries:1,fullTransaction:true});const b=brief(r,value);if(b.status==='FINALIZED')return {receipt:r,brief:b};last=b;}catch(e){last={hash,error:e.shortMessage??e.message};}await pause(5000);}throw new Error('Receipt wait exhausted for '+hash+': '+JSON.stringify(last));}
async function write(label,account,functionName,args=[],value=0n){const hash=await client.writeContract({account,address:CONTRACT,functionName,args,value});const {receipt,brief:b}=await wait(hash,value);entries.push({label,...b});await save();console.log(label+': '+JSON.stringify(b));if(b.execution_result!=='SUCCESS')throw new Error(label+' did not execute successfully: '+JSON.stringify(b));return {hash,receipt};}
async function read(label,functionName,args=[]){const v=await client.readContract({address:CONTRACT,functionName,args});entries.push({label,readback:clean(v)});await save();return v;}
async function body(url){const r=await fetch(url), b=Buffer.from(await r.arrayBuffer());return {status:r.status,digest:createHash('sha256').update(b).digest('hex')};}
async function lifecycle(id,profile,spec,criterion,url,expected){
 await write(id+':create',buyer,'create_agreement',[provider.address,profile,spec,[criterion],0]);
 await write(id+':accept',provider,'accept_agreement',[id]);
 await write(id+':fund',buyer,'fund_agreement',[id,AMOUNT],AMOUNT);
 await write(id+':freeze',buyer,'freeze_agreement',[id,false]);
 const b=await body(url);if(b.status>=500)throw new Error('Evidence endpoint unavailable: '+url+' '+b.status);
 await write(id+':evidence',provider,'submit_evidence',[id,url,b.digest,JSON.stringify({criterion_id:'c1'})]);
 await write(id+':evaluate',provider,'request_evaluation',[id]);
 const state=await read(id+':state-after-eval','get_agreement',[id]);
 const e=await read(id+':evaluation','get_evaluation',[state.latest_evaluation_id]);
 console.log(id+':finding '+JSON.stringify({overall_finding:e.overall_finding,findings:e.findings}));
 if(expected&&e.overall_finding!==expected)throw new Error(id+' actual finding differs from expected: '+e.overall_finding);
 await write(id+':finalize:buyer',buyer,'finalize_verdict',[id]);
 await write(id+':finalize:provider',provider,'finalize_verdict',[id]);
 await write(id+':settle',buyer,'settle',[id]);
 const settlement=await read(id+':settlement','get_settlement',[id]);
 const claimable=BigInt(await read(id+':buyer-claimable','get_claimable',[buyer.address]));
 if(claimable>0n){const before=await client.getBalance({address:buyer.address});const tx=await write(id+':withdraw:buyer',buyer,'withdraw');for(const h of await client.getTriggeredTransactionIds({hash:tx.hash})){const c=await wait(h);entries.push({label:id+':withdraw-child',...c.brief});await save();}const after=await client.getBalance({address:buyer.address});entries.push({label:id+':buyer-balance-delta',before:String(before),after:String(after),delta:String(after-before)});await save();}
 return {evaluation:e,settlement};
}
console.log('ACTORS '+JSON.stringify({chainId:await client.getChainId(),contract:CONTRACT,buyer:buyer.address,provider:provider.address}));
const rl=createInterface({input:stdin,output:stdout});await rl.question('Fund each actor with 0.001 GEN via the configured wallet, then press Enter: ');rl.close();
if(await client.getBalance({address:buyer.address})<AMOUNT*2n||await client.getBalance({address:provider.address})<1n)throw new Error('Actors not sufficiently funded');
await lifecycle('8','api_delivery','GET /json with intentionally incorrect title assertion',{id:'c1',description:'The response slideshow title is exactly NOT THE REAL TITLE',priority:'required',evidence_method:'http',expected_json:{slideshow:{title:'NOT THE REAL TITLE'}},target_url:'https://httpbin.org/json'},'https://httpbin.org/json','FAIL');
await lifecycle('9','ai_agent_delivery','Artifact must contain a slideshow JSON object with title and slides array',{id:'c1',description:'Fetched artifact is valid JSON containing a slideshow object with title and slides array',priority:'required',evidence_method:'artifact:c1',target_url:'https://httpbin.org/robots.txt'},'https://httpbin.org/robots.txt','FAIL');
console.log('Evidence written: '+path);
