#!/usr/bin/env python3
"""Transport-only ordered C90 selector batching; frozen scientific source unchanged.

Full frozen 347-selector class validation remains external and mandatory.
"""
import argparse, hashlib, json, pathlib, os

# The source-locked custody predicates use asserts: optimized Python cannot bypass them.
if not __debug__:
    raise SystemExit("C90_BATCH_CUSTODY_FAIL_CLOSED_PYTHON_OPTIMIZATION")
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):
    o=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):o.update(b)
    return o.hexdigest()
def lines(p):
    b=p.read_bytes()
    assert b.endswith(b'\n') and b'\r' not in b and b'\x00' not in b
    return b.splitlines(keepends=True)
def commit(p,b):
    assert not p.exists(), "refuse overwrite"
    tmp=p.with_name(p.name+'.partial')
    with tmp.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
HEAD="675865123437c3d6c908c7a3af337fd4023c5d0b"
ACTIVATION="0c1f5591a097adc285dec4cbfc320eeebd2c65d3"
GRAPHS={
"sum_product_bsc_p_0_1":("0","2efe52e17c6d66920b23738987818184657caf479c60c78712dff6db4a306bde"),
"soft_tropical_base_2":("1","9647b3e7fb2ee7f6f87d7e3fe6ce6779bd756e100f86f3dc13e7dc5385b5df9a"),
"min_plus_hamming":("2","dd58a7e0c59626032d8714827d9f1097a33a78fd426c7d972407b32340890bb0"),
}
def plan(inp,out,batch,logical_class,algebra):
    assert batch==16 and 0<=logical_class<256 and algebra in GRAPHS
    src=lines(inp);assert len(src)==347
    parsed=[]
    for i,row in enumerate(src):
        bits=row.decode('ascii').strip().split()
        assert len(bits)==2
        idx,coord=map(int,bits)
        assert idx==i*256+logical_class
        assert 0<=coord<(1<<49)
        parsed.append((idx,coord))
    assert len(set(idx for idx,_ in parsed))==347
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    manifest={'schema':'C90_BATCH_TRANSPORT/1','input_sha256':sha(b''.join(src)),'selector_count':347,'logical_class':logical_class,'batch_size':batch,'entries':[],'algebra':algebra,'source_head':HEAD,'activation_head':ACTIVATION,'native_graph_sha256':GRAPHS[algebra][1],'quality_exposed':False}
    for number,start in enumerate(range(0,347,batch)):
        rows=src[start:start+batch]
        filename=f'batch-{number:03d}.selectors.txt'
        commit(out/filename,b''.join(rows))
        manifest['entries'].append({'number':number,'start':start,'count':len(rows),'selector_sha256':sha(b''.join(rows)),'selector_file':filename,'first_selector_index':parsed[start][0],'last_selector_index':parsed[start+len(rows)-1][0]})
    commit(out/'manifest.json',(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode())
    print('BATCH_PLAN_OK',len(manifest['entries']),'SELECTORS',len(src))
def join(folder,output):
    m=json.loads((folder/'manifest.json').read_text())
    assert m['schema']=='C90_BATCH_TRANSPORT/1' and m['selector_count']==347
    assert isinstance(m.get('logical_class'),int) and 0<=m['logical_class']<256
    assert m.get('algebra') in GRAPHS and m.get('source_head')==HEAD and m.get('activation_head')==ACTIVATION
    assert m.get('native_graph_sha256')==GRAPHS[m['algebra']][1] and m.get('quality_exposed') is False
    assert m.get('batch_size')==16 and len(m['entries'])==22
    allsel=b'';allrows=b'';seen=set();pos=0;engine_sha=None
    for index,e in enumerate(m['entries']):
        assert e['number']==index and e['start']==pos and e['count']==min(m['batch_size'],347-pos)
        sel=lines(folder/e['selector_file'])
        assert len(sel)==e['count'] and sha(b''.join(sel))==e['selector_sha256']
        for j,r in enumerate(sel):
            assert int(r.split()[0])==(pos+j)*256+m['logical_class']
        allsel+=b''.join(sel)
        result=folder/f'batch-{index:03d}.rows.jsonl'
        rr=lines(result)
        assert len(rr)==e['count'],(result,len(rr),e['count'])
        for s,r in zip(sel,rr):
            idx,coordinate=map(int,s.decode('ascii').split())
            obj=json.loads(r)
            assert obj['selector_index']==idx and obj['selector_coordinate']==coordinate
            assert obj['algebra_id']==int(GRAPHS[m['algebra']][0])
            assert obj['quality_exposed'] is False and obj['status']=='C90_COMPACT_NATIVE_SELECTOR_EVALUATED'
            assert idx not in seen
            seen.add(idx)
        receipt=folder/f'batch-{index:03d}.verified.json'
        assert receipt.is_file() and not receipt.is_symlink(),receipt
        claim=json.loads(receipt.read_text())
        assert claim['record_type']=='QTR_C90_FROZEN_NATIVE_BATCH_CUSTODY/1'
        assert claim['source_head']==HEAD and claim['activation_head']==ACTIVATION
        assert claim['logical_class']==m['logical_class'] and claim['algebra']==m['algebra']
        assert claim['native_graph_sha256']==m['native_graph_sha256']
        assert claim['batch']==index and claim['count']==e['count'] and claim['start']==pos
        assert claim['selectors_sha256']==e['selector_sha256'] and claim['rows_sha256']==sha(b''.join(rr))
        assert claim['quality_exposed'] is False and claim['status']=='NATIVE_BATCH_VERIFIED__NO_SCIENTIFIC_PROMOTION'
        assert isinstance(claim['evaluator_sha256'],str) and len(claim['evaluator_sha256'])==64
        if engine_sha is None:engine_sha=claim['evaluator_sha256']
        assert engine_sha==claim['evaluator_sha256']
        allrows+=b''.join(rr)
        pos+=e['count']
    assert pos==len(seen)==347 and sha(allsel)==m['input_sha256']
    commit(output,allrows)
    print('BATCH_REASSEMBLY_OK',pos,'ROWS_SHA256',sha(allrows))
def verify(folder,batch,evaluator,graph):
    m=json.loads((folder/'manifest.json').read_text())
    assert m['schema']=='C90_BATCH_TRANSPORT/1' and m['source_head']==HEAD and m['activation_head']==ACTIVATION
    assert m['selector_count']==347 and m['batch_size']==16 and len(m['entries'])==22
    assert m['algebra'] in GRAPHS and m['native_graph_sha256']==GRAPHS[m['algebra']][1]
    assert 0<=batch<len(m['entries']) and m['quality_exposed'] is False
    assert m['logical_class'] in range(256) and m['entries'][batch]['start']==16*batch
    assert not evaluator.is_symlink() and evaluator.is_file()
    assert not graph.is_symlink() and graph.is_file()
    assert h(graph)==GRAPHS[m['algebra']][1], 'ORIGINAL_COMPILED_GRAPH_IDENTITY_DRIFT'
    e=m['entries'][batch]
    selector=folder/e['selector_file'];output=folder/f"batch-{batch:03d}.rows.jsonl"
    selector_lines=selector.read_bytes().splitlines();rr=output.read_bytes().splitlines()
    assert len(selector_lines)==len(rr)==e['count'] and h(selector)==e['selector_sha256']
    for j,(s,r) in enumerate(zip(selector_lines,rr)):
        i,c=map(int,s.split()); obj=json.loads(r)
        assert i==(e['start']+j)*256+m['logical_class']
        assert obj['selector_index']==i and obj['selector_coordinate']==c
        assert obj['algebra_id']==int(GRAPHS[m['algebra']][0])
        assert obj['status']=='C90_COMPACT_NATIVE_SELECTOR_EVALUATED' and obj['quality_exposed'] is False
    evidence={'record_type':'QTR_C90_FROZEN_NATIVE_BATCH_CUSTODY/1',
        'source_head':HEAD,'activation_head':ACTIVATION,'algebra':m['algebra'],
        'logical_class':m['logical_class'],'batch':batch,'start':e['start'],'count':e['count'],
        'native_graph_sha256':m['native_graph_sha256'],'evaluator_sha256':h(evaluator),
        'selectors_sha256':e['selector_sha256'],'rows_sha256':h(output),
        'quality_exposed':False,'status':'NATIVE_BATCH_VERIFIED__NO_SCIENTIFIC_PROMOTION'}
    dest=folder/f"batch-{batch:03d}.verified.json"
    assert not dest.exists(), 'RECEIPT_EXISTS_RECONCILE_BEFORE_RETRY'
    tmp=dest.with_suffix('.partial')
    with tmp.open('xb') as f:
        f.write((json.dumps(evidence,sort_keys=True,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    os.replace(tmp,dest)
    print('C90_NATIVE_BATCH_CUSTODY_VERIFIED',batch,e['count'],evidence['rows_sha256'])


if __name__=='__main__':
    a=argparse.ArgumentParser()
    sub=a.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('plan');p.add_argument('selector_file',type=pathlib.Path);p.add_argument('output_dir',type=pathlib.Path);p.add_argument('--size',type=int,default=16);p.add_argument('--logical-class',type=int,required=True);p.add_argument('--algebra',choices=list(GRAPHS),required=True)
    p=sub.add_parser('verify');p.add_argument('batch_dir',type=pathlib.Path);p.add_argument('batch',type=int);p.add_argument('--evaluator',type=pathlib.Path,required=True);p.add_argument('--graph',type=pathlib.Path,required=True)
    p=sub.add_parser('join');p.add_argument('batch_dir',type=pathlib.Path);p.add_argument('output_file',type=pathlib.Path)
    x=a.parse_args()
    if x.cmd=='plan':plan(x.selector_file,x.output_dir,x.size,x.logical_class,x.algebra)
    elif x.cmd=='verify':verify(x.batch_dir,x.batch,x.evaluator,x.graph)
    else:join(x.batch_dir,x.output_file)
