document.querySelectorAll('nav a').forEach(a=>{if(a.pathname===location.pathname)a.classList.add('active')});
const mode=document.getElementById('id_mode');
function filterItems(){document.querySelectorAll('[data-kind]').forEach(field=>field.hidden=field.dataset.kind!==mode.value)}
if(mode){mode.addEventListener('change',filterItems);filterItems()}
document.querySelectorAll('form[data-processing]').forEach(form=>form.addEventListener('submit',()=>form.classList.add('busy')));

/* Olho de mostrar/ocultar senha nas telas de acesso (login, cadastro,
   recuperação, troca de senha). Só apresentação: o input original mantém
   name, validação e autocomplete. */
document.querySelectorAll('.auth input[type="password"]').forEach((pw)=>{
  const wrap=document.createElement('div');wrap.className='pw-field';
  pw.parentNode.insertBefore(wrap,pw);wrap.appendChild(pw);
  const btn=document.createElement('button');btn.type='button';btn.className='pw-toggle';
  btn.setAttribute('aria-label','Mostrar senha');btn.setAttribute('aria-pressed','false');
  btn.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/><line class="pw-eye-off" x1="4" y1="20" x2="20" y2="4"/></svg>';
  btn.addEventListener('click',()=>{
    const showing=pw.type==='text';
    pw.type=showing?'password':'text';
    btn.setAttribute('aria-label',showing?'Mostrar senha':'Ocultar senha');
    btn.setAttribute('aria-pressed',String(!showing));
    pw.focus();
  });
  wrap.appendChild(btn);
});
