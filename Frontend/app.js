const elQ = document.getElementById('q');
const elBtnSearch = document.getElementById('btnSearch');
const elFile = document.getElementById('file');
const elBtnPredict = document.getElementById('btnPredict');
const elResults = document.getElementById('results');

function renderItems(items){
  elResults.innerHTML = '';
  if(!items || !items.length){ elResults.innerHTML = '<p>No results.</p>'; return; }
  for(const it of items){ elResults.appendChild(card(it)); }
}