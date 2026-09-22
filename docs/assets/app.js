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

  // simple search
  const search = document.getElementById('searchBox');
  if(search){
    search.addEventListener('input', ()=>{
      const q = search.value.toLowerCase();
      document.querySelectorAll('[data-search]').forEach(el=>{
        const text = el.getAttribute('data-search').toLowerCase();
        el.style.display = text.includes(q) ? '' : 'none';
      })
    })
  }
})
