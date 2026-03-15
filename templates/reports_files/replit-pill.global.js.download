"use strict";var ReplitPill=(()=>{(function(){if(typeof window>"u"||typeof document>"u")return;let d=window.self!==window.top;if(d&&document.referrer.startsWith("https://replit-com.web-sandbox.oaiusercontent.com"))return;let m=(()=>{let l=window.location.origin;return!!(l.endsWith(".replit.dev")||l.endsWith(".repl.co"))})(),s=!0,h=document.currentScript?.getAttribute("data-referral-code"),b=()=>{try{let l=!1;try{l=window.localStorage?.getItem("replit-pill-preference")==="hidden"}catch{}if(l||document.getElementById("replit-pill-host"))return;let c=document.createElement("div");c.id="replit-pill-host";let w=c.attachShadow({mode:"closed"}),C=`
        <path d="M0 1.72499C0 0.772305 0.772305 0 1.72499 0H9.77495C10.7276 0 11.4999 0.772305 11.4999 1.72499V9.19996H1.72499C0.772305 9.19996 0 8.42765 0 7.47496V1.72499Z" fill="currentColor"/>
        <path d="M11.4999 9.19996H21.2749C22.2276 9.19996 22.9999 9.97226 22.9999 10.9249V16.6749C22.9999 17.6276 22.2276 18.3999 21.2749 18.3999H11.4999V9.19996Z" fill="currentColor"/>
        <path d="M0 20.1249C0 19.1722 0.772305 18.3999 1.72499 18.3999H11.4999V25.8749C11.4999 26.8276 10.7276 27.5999 9.77495 27.5999H1.72499C0.772305 27.5999 0 26.8276 0 25.8749V20.1249Z" fill="currentColor"/>
      `,E=`
        <path d="M18 6 6 18"></path>
        <path d="m6 6 12 12"></path>
      `,x=document.createElement("style");x.textContent=`
        #replit-pill {
          position: fixed;
          bottom: 48px;
          right: 48px;
          border-radius: 120px;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 12px;
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          z-index: 1000000;
          white-space: nowrap;
          cursor: pointer;
          overflow: hidden;
          background-color: rgba(0, 0, 0, 0.4);
          backdrop-filter: blur(6px);
          -webkit-backdrop-filter: blur(6px);
          color: #f0f2f6;
          box-shadow: 1px 1px 1px 0px rgba(0, 0, 0, 0.05), 1px 1px 1px 0px rgba(255, 255, 255, 0.1);
          transition: transform 0.2s ease;
        }
        #replit-pill:hover {
          transform: scale(1.05);
        }
        #replit-pill .shimmer {
          position: absolute;
          inset: 0;
          transform: translateX(-100%);
          transition: transform 0.7s ease-in-out;
          background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.1), transparent);
          pointer-events: none;
        }
        #replit-pill:hover .shimmer {
          transform: translateX(100%);
        }
        #replit-pill .badge-content {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          position: relative;
          flex: 0 0 auto;
        }
        #replit-pill .replit-logo {
          color: #f0f2f6;
        }
        #replit-pill .replit-text {
          font-weight: 500;
          line-height: 20px;
          color: #f0f2f6;
        }
        #replit-pill .close-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 2px;
          flex: 0 0 auto;
          border-radius: 64px;
          width: 12px;
          height: 12px;
          min-width: 0;
          cursor: pointer;
          border: none;
          box-sizing: border-box;
          background-color: transparent;
          transition: background-color 0.2s ease;
        }
        #replit-pill .close-button:hover {
          background-color: rgba(255, 255, 255, 0.1);
        }
        #replit-pill .close-button:focus-visible {
          outline: 1px solid #e6e9ef;
          outline-offset: 1px;
        }
        #replit-pill .close-icon {
          width: 8px;
          height: 8px;
          color: #e6e9ef;
        }
      `;let v=(t,o,r,g,p)=>{let e=document.createElementNS("http://www.w3.org/2000/svg","svg");return e.setAttribute("width",t),e.setAttribute("height",o),e.setAttribute("viewBox",r),e.setAttribute("fill","none"),p&&(e.className.baseVal=p),e.innerHTML=g,e},i=document.createElement("div");i.id="replit-pill";let y=document.createElement("div");y.className="shimmer";let u=document.createElement("div");u.className="badge-content";let M=v("16","16","0 0 23 28",C,"replit-logo"),f=document.createElement("div");f.textContent="Made with Replit",f.className="replit-text";let n=document.createElement("button");n.className="close-button",n.setAttribute("aria-label","Close");let a=v("24","24","0 0 24 24",E,"close-icon");a.setAttribute("stroke","currentColor"),a.setAttribute("stroke-width","2"),a.setAttribute("stroke-linecap","round"),a.setAttribute("stroke-linejoin","round"),n.appendChild(a),u.append(M,f),i.append(y,u,n),i.onclick=t=>{if(t.target!==n&&t.target!==n.firstChild){let o=h?`https://replit.com/referral-code/${h}?source=badge&referrer=${encodeURIComponent(window.location.origin)}`:"https://join.replit.com/badge_v3";if(d&&m&&window.parent){let r={type:"CLICKED_MADE_WITH_REPLIT_BADGE"};window.parent.postMessage(r,"*")}else window.open(o,"_blank")}},n.onclick=t=>{t.stopPropagation(),i.style.display="none";try{window.localStorage.setItem("replit-pill-preference","hidden")}catch{}},w.appendChild(x),w.appendChild(i),document.body.appendChild(c),d&&m?window.addEventListener("message",t=>{let o=t.origin,r=new URL(o),g=r.hostname==="replit.com"||r.hostname.endsWith(".replit.com")||r.hostname.endsWith(".replit.dev")||r.hostname.endsWith(".repl.co"),p=!1;if(document.referrer)try{let S=new URL(document.referrer).origin;p=o===S}catch{}if(!g&&!p)return;let e=t.data;if(!(!e||typeof e!="object"||!e.type)){if(e.type==="SHOW_MADE_WITH_REPLIT_BADGE"){if(s)return;i.style.display="inline-flex",s=!0}else if(e.type==="HIDE_MADE_WITH_REPLIT_BADGE"){if(!s)return;i.style.display="none",s=!1}}}):s=!0}catch{}};document.readyState==="complete"||document.readyState==="interactive"?setTimeout(b,100):document.addEventListener("DOMContentLoaded",b)})();})();
