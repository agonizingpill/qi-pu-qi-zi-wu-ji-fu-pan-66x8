import {request} from './api.js';
import {actionForm} from './controls.js';
import {el} from './dom.js';
import {dataView, status, titleBlock} from './widgets.js';

function panelFor(section) {
  const panel = el('section', {class:'ledger', 'aria-label':section.caption});
  const refresh = async () => {
    try {
      const rows = await request(section.path);
      const list = section.unwrap ? (rows[section.unwrap] || []) : rows;
      panel.replaceChildren(el('h2',{},section.caption),dataView(list, section.columns,section.view));
    } catch (error) { panel.replaceChildren(status(error.message,'error')); }
  };
  return {panel, refresh};
}

export function workspace(root, role, page) {
  const main = panelFor(page);
  const extras = (page.sections || []).map(section => panelFor(section));
  const refresh = async () => { await Promise.all([main.refresh(), ...extras.map(x => x.refresh())]); };
  const actions = page.actions.filter(x => x.roles.includes(role));
  root.replaceChildren(titleBlock(page.module, page.title, page.detail),
    el('div',{class:'work '+page.layout},main.panel,...extras.map(x => x.panel),
      actions.length ? el('section',{class:'actions'},actions.map(x => actionForm(x, refresh))) : null));
  return refresh();
}
