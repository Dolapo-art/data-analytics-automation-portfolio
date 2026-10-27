// Headless DOM harness: executes the actual inline dashboard JavaScript.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/dashboard.html','utf8');
class Element{constructor(){this.children=[];this.value='';this.textContent='';this.style={};this.events={};}append(...x){this.children.push(...x);}replaceChildren(){this.children=[];}addEventListener(k,fn){this.events[k]=fn;}}
const nodes={};const document={getElementById:id=>nodes[id]??=new Element(),createElement:()=>new Element()};
const ctx=vm.createContext({document,console});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
assert.equal(nodes.count.textContent,'7,043');assert.equal(nodes.churned.textContent,'1,869');
assert.equal(nodes.evaluation.children.length,6);
nodes.Contract.value='Month-to-month';nodes.Contract.events.change();
assert.equal(nodes.count.textContent,'3,875');assert.equal(nodes.churned.textContent,'1,655');
nodes.InternetService.value='not-a-category';nodes.InternetService.events.change();assert.equal(nodes.count.textContent,'0');assert.equal(nodes.rate.textContent,'—');
nodes.reset.events.click();assert.equal(nodes.count.textContent,'7,043');assert.equal(nodes.evaluation.children.length,6);
console.log('PASS: initial totals, contract filter, empty cohort, reset and fixed model metrics.');
