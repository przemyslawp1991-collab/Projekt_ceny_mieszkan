// Resolve the bundled artifact-tool font-data alias without changing its runtime files.
const Module=require('node:module');
const path=require('node:path');
const original=Module._load;
Module._load=function(specifier,parent,...rest){
 if(specifier.startsWith('#standard-fonts/')){
  const alias=specifier.slice('#standard-fonts/'.length);
  const name=alias.replace(/^(Helvetica|Courier)(BoldOblique|Bold|Oblique)$/,'$1-$2').replace(/^Times(BoldItalic|Bold|Italic|Roman)$/,'Times-$1');
  const lib=original.call(this,path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@pdf-lib/standard-fonts'),parent,...rest);
  const f=lib.Font.load(name),names=f.CharMetrics.map(x=>x.N),index=new Map(names.map((n,i)=>[n,i])),groups=new Map();
  for(const [a,b,k]of f.KernPairs??[]){if(!index.has(a)||!index.has(b))continue;const arr=groups.get(k)??[];arr.push(index.get(a)*names.length+index.get(b));groups.set(k,arr);}
  const kernPairs=[];for(const[k,values]of groups){values.sort((a,b)=>a-b);let last=0;kernPairs.push(k,values.map(v=>{const d=v-last;last=v;return d;}));}
  return {name:f.FontName,bbox:f.FontBBox,ascender:f.Ascender??0,descender:f.Descender??0,xHeight:f.XHeight??0,capHeight:f.CapHeight??0,glyphNames:names.join(' '),glyphWidths:f.CharMetrics.map(x=>x.WX),kernPairs};
 }
 return original.call(this,specifier,parent,...rest);
};
