document.querySelectorAll('nav a').forEach(a=>{if(a.pathname===location.pathname)a.classList.add('active')});
const mode=document.getElementById('id_mode');
function filterItems(){document.querySelectorAll('[data-kind]').forEach(field=>field.hidden=field.dataset.kind!==mode.value)}
if(mode){mode.addEventListener('change',filterItems);filterItems()}
document.querySelectorAll('form[data-processing]').forEach(form=>form.addEventListener('submit',()=>form.classList.add('busy')));
