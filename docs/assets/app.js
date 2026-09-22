document.addEventListener('DOMContentLoaded', ()=>{
  const tocLinks = document.querySelectorAll('.toc a');
  const sections = [...document.querySelectorAll('section[id]')];
  const observer = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        tocLinks.forEach(a=>a.classList.remove('active'));
        const id = e.target.id;
        const link = document.querySelector(`.toc a[href="#${id}"]`);
        if(link) link.classList.add('active');
      }
    })
  }, {rootMargin:'-40% 0px -50% 0px'});
  sections.forEach(s=>observer.observe(s));

  // simple search - searches section text content
  const search = document.getElementById('searchBox');
  if(search){
    search.addEventListener('input', ()=>{
      const q = search.value.toLowerCase().trim();
      document.querySelectorAll('section[id]').forEach(el=>{
        const text = (el.textContent || '').toLowerCase();
        const dataSearch = el.getAttribute('data-search') || '';
        const combined = text + ' ' + dataSearch.toLowerCase();
        if(!q){
          el.style.display = '';
        } else {
          el.style.display = combined.includes(q) ? '' : 'none';
        }
      })
    })
  }
})
