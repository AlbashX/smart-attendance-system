"""Run the official 10-fold LFW pairs file with frozen YuNet/SFace.

No dataset is downloaded. Supply lawfully obtained LFW images and pairs.txt.
Each fold's threshold is selected using the other nine folds only.
Detection/quality failures count as incorrect in end-to-end accuracy; conditional
verification metrics are additionally reported for successfully processed pairs.
"""
import argparse
import base64
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.vision import FaceEngine
from backend.core import verification_metrics


def parse_pairs(path, root):
    lines=path.read_text().strip().splitlines()
    header=lines[0].split()
    if header != ['10','300']:
        raise ValueError('Expected official 10-fold pairs.txt header: 10 300')
    if len(lines)-1 != 6000: raise ValueError('Expected 6000 pairs')
    pairs=[]
    for index,line in enumerate(lines[1:]):
        fields=line.split()
        if len(fields)==3:
            name,a,b=fields
            left=root/name/f'{name}_{int(a):04d}.jpg'
            right=root/name/f'{name}_{int(b):04d}.jpg'
            same=True
        elif len(fields)==4:
            n1,a,n2,b=fields
            left=root/n1/f'{n1}_{int(a):04d}.jpg'
            right=root/n2/f'{n2}_{int(b):04d}.jpg'
            same=False
        else: raise ValueError(f'Invalid pair on line {index+2}')
        pairs.append((index//600,left,right,same))
    return pairs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images',type=Path,required=True)
    parser.add_argument('--pairs',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('data/lfw_report.json'))
    args=parser.parse_args()
    pairs=parse_pairs(args.pairs,args.images)
    missing={str(p) for _,a,b,_ in pairs for p in (a,b) if not p.exists()}
    if missing: raise ValueError(f'{len(missing)} images missing; first: {next(iter(missing))}')
    engine=FaceEngine()
    cache={}
    failures={}
    latency=[]
    def embed(path):
        if path not in cache:
            result=engine.extract(base64.b64encode(path.read_bytes()).decode())
            cache[path]=result.get('embedding')
            latency.append(result['latency_ms'])
            if cache[path] is None: failures[str(path)]=result['reason']
        return cache[path]
    observations=[]
    for i,(fold,a,b,same) in enumerate(pairs):
        va,vb=embed(a),embed(b)
        score=float(np.clip(np.dot(va,vb),-1,1)) if va is not None and vb is not None else None
        observations.append(dict(fold=fold,same=same,score=score))
        if (i+1)%100==0: print(f'{i+1}/6000 pairs',flush=True)
    folds=[]
    for fold in range(10):
        train=[r for r in observations if r['fold']!=fold and r['score'] is not None]
        test=[r for r in observations if r['fold']==fold]
        if not train: raise ValueError('No valid training-fold pairs')
        # Threshold sweep uses only nine development folds, not the held-out fold.
        thresholds=np.linspace(-1,1,2001)
        scores=np.array([r['score'] for r in train])
        labels=np.array([r['same'] for r in train])
        threshold=float(max(thresholds,key=lambda t:float(np.mean((scores>=t)==labels))))
        valid=[r for r in test if r['score'] is not None]
        correct=sum((r['score']>=threshold)==r['same'] for r in valid)
        folds.append(dict(fold=fold+1,threshold=threshold,pairs=len(test),failed_pairs=len(test)-len(valid),
                          end_to_end_accuracy=correct/len(test),
                          conditional_verification=verification_metrics([r['score'] for r in valid if r['same']],
                                                                        [r['score'] for r in valid if not r['same']],threshold)))
    report=dict(protocol='Official 10-fold pair definitions; frozen external pretrained models; quality gate enabled',
                model='YuNet 2023mar + SFace 2021dec',folds=folds,
                mean_end_to_end_accuracy=float(np.mean([f['end_to_end_accuracy'] for f in folds])),
                std_across_folds=float(np.std([f['end_to_end_accuracy'] for f in folds])),
                unique_images=len(cache),failed_images=len(failures),failure_reasons=failures,
                extraction_latency_median_ms=float(np.median(latency)),
                caveats=['Pretraining data overlap has not been independently audited.',
                         'Quality gates differ from published SFace benchmarks; do not compare as identical protocols.',
                         'Not a measure of local open-set attendance recognition.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print(f'Report written to {args.output}')


if __name__=='__main__': main()
