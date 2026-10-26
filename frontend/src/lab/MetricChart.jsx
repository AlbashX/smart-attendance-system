import {useEffect,useRef} from 'react';
import {Chart,LineController,LineElement,PointElement,LinearScale,CategoryScale,Tooltip,Legend} from 'chart.js';
Chart.register(LineController,LineElement,PointElement,LinearScale,CategoryScale,Tooltip,Legend);

export default function MetricChart({title,labels,series,theme,roc=false,unitInterval=false}) {
  const ref=useRef(null);
  useEffect(()=>{
    if (!series.some(s=>s.values.length)) return;
    const color=theme==='dark'?'#c5d4e6':'#52647e';
    const grid=theme==='dark'?'#2a3e54':'#edf1f5';
    const chart=new Chart(ref.current,{
      type:'line',
      data:{labels,datasets:series.map((s,i)=>({label:s.name,data:s.values,
        borderColor:s.color,backgroundColor:s.color,pointRadius:roc?2:3,borderWidth:2,
        tension:0,fill:false,borderDash:roc&&i===1?[5,5]:[]}))},
      options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{position:'bottom',labels:{color,usePointStyle:true,boxWidth:8}},
          tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${Number(c.parsed.y).toFixed(4)}`}}},
        scales:{x:{type:roc?'linear':'category',min:roc?0:undefined,max:roc?1:undefined,
          title:{display:true,text:roc?'False positive rate':'Epoch',color},ticks:{color,maxTicksLimit:8},grid:{color:grid}},
          y:{min:0,max:unitInterval||roc?1:undefined,ticks:{color},grid:{color:grid},
            title:{display:true,text:roc?'True positive rate':title,color}}}}
    });
    return ()=>chart.destroy();
  },[title,labels,series,theme,roc,unitInterval]);
  return <div className="lab-chart"><canvas ref={ref} role="img" aria-label={title}/></div>;
}
