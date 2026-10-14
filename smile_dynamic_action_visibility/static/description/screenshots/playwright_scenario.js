// Usage: node scenario.js <screenshot_dir>
const { chromium } = require('playwright');
const OUT = process.argv[2];
const BASE = 'http://localhost:8069';
const results = [];
function check(name, cond, detail) { results.push({name, ok: !!cond, detail}); }
(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({viewport: {width: 1400, height: 700}});
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`${BASE}/web/login?db=odoo`);
  await page.fill('input[name=login]', 'admin');
  await page.fill('input[name=password]', 'admin');
  await page.click('button[type=submit]');
  await page.waitForSelector('.o_main_navbar', {timeout: 30000});

  const menuItems = async () => {
    try {
      await page.waitForSelector('.o-dropdown--menu .dropdown-item', {timeout: 10000});
    } catch (e) {
      await page.screenshot({path: `${OUT}/failure.png`});
      console.log('ERRORS', errors.join('\n---\n'));
      throw e;
    }
    await page.waitForTimeout(500);
    return (await page.locator('.o-dropdown--menu .dropdown-item').allInnerTexts()).map(s => s.trim());
  };
  const closeMenu = async () => {
    if (await page.locator('.o-dropdown--menu').count()) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    }
  };
  const openMenu = async (label) => {
    await closeMenu();
    await page.locator('.o_control_panel button', {hasText: label}).first().click();
    return menuItems();
  };
  const row = (name) => page.locator('.o_data_row', {hasText: name}).locator('.o_list_record_selector input');
  const shot = (f) => page.screenshot({path: `${OUT}/${f}`});

  // 0. Rules configuration
  await page.goto(`${BASE}/odoo/action-smile_dynamic_action_visibility.action_dynamic_action_rule`);
  await page.waitForSelector('.o_list_view .o_data_row');
  await shot('01_rules_list.png');
  await page.locator('.o_data_row', {hasText: 'No merge on companies'}).click();
  await page.waitForSelector('.o_form_view');
  await shot('02_rule_form.png');

  await page.goto(`${BASE}/odoo/action-base.action_partner_form?view_type=list`);
  await page.waitForSelector('.o_list_view .o_data_row');

  // A. Person selected: Merge visible
  await row('Bob Martin').check();
  let items = await openMenu('Actions');
  check('A. Bob selected -> Merge visible', items.includes('Merge'), items);
  await shot('03_person_selected_merge_visible.png');

  // B. Add a company to the selection (selection change -> nextProps): Merge hidden
  await closeMenu();
  await row('Alpha SA').check();
  await page.waitForTimeout(800);
  items = await openMenu('Actions');
  check('B. Bob+Alpha selected -> Merge hidden', !items.includes('Merge'), items);
  await shot('04_company_added_merge_hidden.png');

  // C. Remove the company again: Merge back
  await closeMenu();
  await row('Alpha SA').uncheck();
  await page.waitForTimeout(800);
  items = await openMenu('Actions');
  check('C. Alpha unselected -> Merge visible again', items.includes('Merge'), items);
  await shot('05_company_removed_merge_back.png');

  // D. Print: partner with email -> report visible
  items = await openMenu('Print');
  check('D. Bob selected -> Partner Sheet printable', items.includes('Partner Sheet'), items);
  await shot('06_print_with_email_visible.png');

  // E. Print: partner without email -> report hidden
  await closeMenu();
  await row('Bob Martin').uncheck();
  await row('Carla Dupont').check();
  await page.waitForTimeout(800);
  items = await openMenu('Print');
  check('E. Carla (no email) -> Partner Sheet hidden', !items.includes('Partner Sheet'), items);
  await shot('07_print_without_email_hidden.png');

  // F. Form view (cog menu), partner with email: report printable
  await closeMenu();
  await row('Carla Dupont').uncheck();
  await page.waitForTimeout(500);
  await page.locator('.o_data_row', {hasText: 'Bob Martin'}).locator('td.o_data_cell').first().click();
  await page.waitForSelector('.o_form_view');
  const openCog = async () => {
    await closeMenu();
    await page.locator('.o_control_panel .o_cp_action_menus button').first().click();
    return menuItems();
  };
  const formName = () => page.locator('.o_form_view .o_field_widget[name=name] input, .o_form_view .o_field_widget[name=name] textarea').first().inputValue();
  items = await openCog();
  check(`F. Form ${await formName()} (cog menu) -> Partner Sheet visible`, items.includes('Partner Sheet'), items);
  await shot('08_form_with_email_report_visible.png');

  // G. Pager to the next record (Carla, no email): report hidden (record change -> nextProps)
  await closeMenu();
  await page.locator('.o_pager_next').click();
  await page.waitForFunction(() => {
    const el = document.querySelector('.o_form_view .o_field_widget[name=name] input, .o_form_view .o_field_widget[name=name] textarea');
    return el && el.value === 'Carla Dupont';
  }, null, {timeout: 10000});
  await page.waitForTimeout(800);
  items = await openCog();
  check(`G. Form next record ${await formName()} -> Partner Sheet hidden`, !items.includes('Partner Sheet'), items);
  await shot('09_form_next_record_report_hidden.png');

  await b.close();
  for (const r of results) console.log(r.ok ? 'PASS' : 'FAIL', r.name, JSON.stringify(r.detail));
  if (errors.length) console.log('CONSOLE ERRORS', errors);
  process.exit(results.every(r => r.ok) ? 0 : 1);
})().catch(async e => { console.error(e); process.exit(2); });
