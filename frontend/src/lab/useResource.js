import {useEffect, useState} from 'react';
import {api} from '../api';

// Abort requests when a filter changes. Keyed state also prevents a one-frame stale report.
export function useResource(path, revision=0) {
  const key = `${path}:${revision}`;
  const [state,setState]=useState({key:null,data:null,error:null,loading:false});
  useEffect(()=>{
    if (!path) return;
    const controller=new AbortController();
    setState({key,data:null,error:null,loading:true});
    api(path,{signal:controller.signal}).then(data=>{
      if (!controller.signal.aborted) setState({key,data,error:null,loading:false});
    }).catch(error=>{
      if (!controller.signal.aborted) setState({key,data:null,error:error.message,loading:false});
    });
    return ()=>controller.abort();
  },[path,key]);
  return state.key===key ? state : {data:null,error:null,loading:!!path};
}
