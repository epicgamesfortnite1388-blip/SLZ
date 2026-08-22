<!--
SLZ ERP — Task 002 deliverable
Business Review / سند بازنگری کسب‌وکار (FA/EN)
Intended for print as ~1 A4 landscape page. Source: docs/business-analysis/ (Task 001).
Status legend: OPEN = awaiting SLZ decision.
-->

# SLZ ERP — Business Review Workshop / کارگاه بازنگری کسب‌وکار

**Made-to-order flexible packaging · صنایع لفاف زرین** — Prepared from Task 001 discovery. Version 0.1 (draft for workshop) — 2026-08-20.

---

## A. Purpose / هدف جلسه

**EN —** Validate the **business model and processes** before any ERP software is built. This meeting is **not a software demo**; it is a **business-process validation workshop**. We must convert analyst assumptions and open questions into decisions SLZ owns, so the software team does not code guesses.

**FA —** هدف، **اعتبارسنجی مدل و فرایندهای کسب‌وکار** پیش از ساخت نرم‌افزار ERP است. این جلسه **نمایش نرم‌افزار نیست**؛ بلکه **کارگاه اعتبارسنجی فرایند کسب‌وکار** است. باید فرض‌ها و پرسش‌های باز را به تصمیم‌هایی تبدیل کنیم که در مالکیت مجموعهٔ زرین باشد تا تیم نرم‌افزار بر پایهٔ حدس کدنویسی نکند.

---

## B. Critical Decisions / تصمیم‌های کلیدی (ranked by implementation impact)

> 15 highest-impact items selected from the 64 open questions. Ranked by how deeply they change database, product, BOM, routing, planning, inventory, costing, quality, sales, approval, permissions, and traceability. / پانزده مورد پراثرترین از میان ۶۴ پرسش باز، بر اساس میزان تأثیر بر پایگاه‌داده و مدل.

| # | ID | Decision / تصمیم | Why it matters / اهمیت | Owner / مسئول | Status |
|---|----|------------------|------------------------|---------------|--------|
| 1 | Q-046 | Serialize each **roll** as a unique tracked object, or track rolls only by lot + count? / سریال‌گذاری هر **رول** یا ردیابی فقط با شماره بچ و تعداد؟ | Foundational to DB schema, genealogy & costing; hard to change later. / پایهٔ ساختار پایگاه‌داده، شجره‌نامه و بهای تمام‌شده. | Production + Warehouse / تولید و انبار | OPEN |
| 2 | Q-026 | Which **intermediates** (base film, printed, laminate, slit rolls) are inventoried vs flow-through? / کدام محصولات نیمه‌ساخته انبار می‌شوند و کدام عبوری‌اند؟ | Determines number of real **BOM levels** & WIP tracking. / تعیین‌کنندهٔ تعداد سطوح BOM و ردیابی حین‌ساخت. | Planning + Production / برنامه‌ریزی و تولید | OPEN |
| 3 | Q-049 | Required **traceability granularity**: per roll / pallet / carton? / سطح ردیابی موردنیاز: رول، پالت یا کارتن؟ | Drives lot model, recall capability, label design. / تعیین مدل بچ، قابلیت فراخوان و طراحی برچسب. | Quality + Warehouse / کیفیت و انبار | OPEN |
| 4 | Q-019 | Internal **product code** independent of customer code? Numbering scheme? / کد داخلی محصول مستقل از کد مشتری؟ الگوی کدگذاری؟ | Shapes product-identity model & every downstream reference. / شکل‌دهی مدل هویت محصول و ارجاعات بعدی. | Sales + Engineering / فروش و مهندسی | OPEN |
| 5 | Q-024 | What triggers a **new spec revision** vs a minor correction, and who approves? / چه چیزی نسخهٔ جدید مشخصات را ایجاب می‌کند و تأییدکننده کیست؟ | Core to versioning/history & auditability. / پایهٔ نسخه‌بندی، تاریخچه و حسابرسی‌پذیری. | Engineering + Management / مهندسی و مدیریت | OPEN |
| 6 | Q-027 | **BOM consumption basis** (per piece / area / weight / length) & standard waste factors? / مبنای مصرف BOM و ضرایب استاندارد ضایعات؟ | Determines BOM math, MRP accuracy & material cost. / تعیین محاسبات BOM، دقت MRP و بهای مواد. | Engineering + Production / مهندسی و تولید | OPEN |
| 7 | Q-029 | Standard **routings per product group** and typical stage skips? / مسیرهای تولید استاندارد به تفکیک گروه محصول و مراحل قابل‌حذف؟ | Defines routing templates & scheduling scope. / تعریف الگوهای مسیر و دامنهٔ زمان‌بندی. | Planning + Production / برنامه‌ریزی و تولید | OPEN |
| 8 | Q-002 | Share of **repeat vs new-product** orders → how much to automate each path? / نسبت سفارش‌های تکراری به محصول جدید؟ | Splits sales/engineering workflow into two paths. / تفکیک گردش‌کار فروش/مهندسی به دو مسیر. | Sales + Management / فروش و مدیریت | OPEN |
| 9 | Q-003 | Is **sample / first-article sign-off** required per new job (and for repeats)? / آیا تأیید نمونه/سری اول برای هر کار جدید (و تکراری) لازم است؟ | Adds an approval loop before bulk production. / افزودن حلقهٔ تأیید پیش از تولید انبوه. | Sales + Quality / فروش و کیفیت | OPEN |
| 10 | Q-006 | **Over/under-delivery tolerance** (±%) commercial rule? / قاعدهٔ تجاری رواداری تحویل کمتر/بیشتر (±٪)؟ | Affects order fulfilment, invoicing & unit cost. / اثر بر تکمیل سفارش، صورتحساب و بهای واحد. | Management + Sales / مدیریت و فروش | OPEN |
| 11 | Q-034 | **Material valuation**: FIFO / weighted-average / lot-actual? / روش ارزش‌گذاری مواد: FIFO / میانگین موزون / واقعی به تفکیک بچ؟ | Determines inventory valuation & cost engine. / تعیین ارزش‌گذاری موجودی و موتور بهای تمام‌شده. | Finance / مالی | OPEN |
| 12 | Q-033 | **Cost rates & allocation drivers** (labor/machine/energy/maintenance/overhead)? / نرخ‌ها و محرک‌های تخصیص هزینه؟ | Without these, actual costing cannot be computed. / بدون این‌ها بهای تمام‌شدهٔ واقعی محاسبه نمی‌شود. | Finance + Production / مالی و تولید | OPEN |
| 13 | Q-048 | **Backflush** vs explicit **lot/roll issue** on the floor? / مصرف خودکار (backflush) یا صدور دستی بچ/رول؟ | Trade-off: data-entry effort vs traceability precision. / توازن بین بار ثبت داده و دقت ردیابی. | Production + Warehouse / تولید و انبار | OPEN |
| 14 | Q-054 | **Approval thresholds & hierarchy** (PO limits, discount limits, multi-step)? / آستانه‌ها و سلسله‌مراتب تأیید؟ | Defines approval engine & permissions model. / تعریف موتور تأیید و مدل دسترسی. | Management + Finance / مدیریت و مالی | OPEN |
| 15 | Q-062 | Shop-floor data capture: **manual** entry vs **machine/PLC** integration? / ثبت دادهٔ کف کارگاه: دستی یا یکپارچگی با ماشین/PLC؟ | Determines feasibility of real-time trace & OEE. / تعیین امکان ردیابی لحظه‌ای و OEE. | Production + Management / تولید و مدیریت | OPEN |

## C. Assumptions to confirm / فرض‌هایی که باید تأیید شوند (A-001…A-022)

> These are analyst industry-defaults, **not** confirmed requirements. Confirm, correct, or reject each. / این‌ها پیش‌فرض‌های کارشناسی صنعت‌اند، نه الزامات تأییدشده. هر مورد را تأیید، اصلاح یا رد کنید.

| Category / دسته | IDs | Short description / شرح کوتاه | Impact if wrong / اثر خطا | Owner / مسئول | Status |
|-----------------|-----|------------------------------|---------------------------|---------------|--------|
| Sales / فروش | A-001, A-006 | New-vs-repeat paths; reverse flows (RMA, over/under, change orders) exist. / مسیر جدید/تکراری؛ وجود جریان‌های بازگشتی. | Wrong sales workflow & order lifecycle. / گردش‌کار و چرخهٔ سفارش نادرست. | Sales / فروش | OPEN |
| Product Eng. / مهندسی محصول | A-002, A-003, A-012, A-014 | Sampling loop; tooling as its own object; area/weight BOM consumption; alternate materials. / نمونه‌گیری؛ کلیشه به‌عنوان موجودیت مستقل؛ مصرف بر پایهٔ سطح/وزن؛ مواد جایگزین. | Wrong product/BOM model. / مدل محصول و BOM نادرست. | Engineering / مهندسی | OPEN |
| Manufacturing / تولید | A-007, A-008, A-009, A-010, A-013 | Process chain order; curing/aging; slitting 1→N; final inspection/packing; setup vs running waste. / ترتیب زنجیرهٔ فرایند؛ کیورینگ؛ برش ۱→N؛ بازرسی نهایی؛ ضایعات راه‌اندازی/جریان. | Wrong routing & genealogy. / مسیر و شجره‌نامهٔ نادرست. | Production / تولید | OPEN |
| Planning / برنامه‌ریزی | A-011, A-019 | Expected yield/scrap % per stage; reservations = soft allocation. / بازده/ضایعات موردانتظار هر مرحله؛ رزرو نرم. | Wrong MRP & scheduling. / MRP و زمان‌بندی نادرست. | Planning / برنامه‌ریزی | OPEN |
| Inventory / انبار | A-009, A-020, A-021 | Roll genealogy; lot shelf-life/expiry; multi-UoM conversions. / شجره‌نامهٔ رول؛ انقضای بچ؛ تبدیل واحدها. | Wrong stock & trace model. / مدل موجودی و ردیابی نادرست. | Warehouse / انبار | OPEN |
| Quality / کیفیت | A-005, A-010, A-018 | Inline QC at every stage; defined inspection points. / کنترل کیفیت حین هر مرحله؛ نقاط بازرسی مشخص. | Missing/incorrect QC gates. / دروازه‌های کیفیت نادرست. | Quality / کیفیت | OPEN |
| Costing / بهای تمام‌شده | A-013, A-015, A-017 | Setup vs running waste; scrap carries accumulated cost; over/under affects unit cost. / ضایعات؛ انتقال هزینهٔ تجمعی ضایعات؛ اثر تحویل کم/زیاد. | Wrong cost figures. / ارقام هزینهٔ نادرست. | Finance / مالی | OPEN |
| Purchasing / خرید | A-004 | Commodity resins stocked; specialty materials bought to order. / رزین‌های عمومی انبار؛ مواد خاص خرید سفارشی. | Wrong MRP/purchasing split. / تفکیک نادرست خرید/MRP. | Purchasing / خرید | OPEN |
| Finance / مالی | A-016, A-017 | Tooling customer-paid or amortized; over/under invoicing. / کلیشه پرداختی مشتری یا مستهلک؛ صورتحساب تحویل کم/زیاد. | Wrong margin & billing. / حاشیه و صورتحساب نادرست. | Finance / مالی | OPEN |
| Security / حاکمیت | A-022 | Proposed role catalogue. / فهرست نقش‌های پیشنهادی. | Wrong permissions/SoD. / دسترسی و تفکیک وظایف نادرست. | Management / مدیریت | OPEN |

---

## D. Department workshop checklist / سیاههٔ کارگاهی به تفکیک واحد

- **Management / مدیریت** — approval authority, commercial policies, priorities, profitability, KPI definitions. Owns: Q-054, Q-006/037, Q-038, Q-057. / اختیار تأیید، سیاست‌های تجاری، اولویت‌ها، سودآوری، تعریف KPI.
- **Sales / فروش** — quotation, customer product, customer approval, order changes, delivery commitments, pricing. Owns: Q-002, Q-003, Q-006, Q-019. / پیش‌فاکتور، محصول مشتری، تأیید مشتری، تغییر سفارش، تعهد تحویل، قیمت‌گذاری.
- **Engineering / Prepress · مهندسی و پری‌پرس** — specifications, artwork, revisions, tooling, technical approval, sampling. Owns: Q-019, Q-021, Q-022, Q-024, Q-025, Q-004/036. / مشخصات، آرت‌ورک، نسخه‌ها، کلیشه، تأیید فنی، نمونه‌گیری.
- **Planning / برنامه‌ریزی** — production priorities, scheduling, capacity, alternative machines, material availability. Owns: Q-011/015, Q-018, Q-029, Q-005/050. / اولویت تولید، زمان‌بندی، ظرفیت، ماشین جایگزین، موجودی مواد.
- **Production / تولید** — actual machine processes, setup, production reporting, downtime, scrap, rework. Owns: Q-010, Q-012, Q-013, Q-016/042, Q-043, Q-062. / فرایند واقعی ماشین، راه‌اندازی، گزارش تولید، توقف، ضایعات، دوباره‌کاری.
- **Quality / کنترل کیفیت** — inspection points, specifications, tolerances, NCR, quarantine, release. Owns: Q-039, Q-040, Q-041, Q-044, Q-045, Q-022. / نقاط بازرسی، مشخصات، رواداری، عدم‌انطباق، قرنطینه، ترخیص.
- **Warehouse / انبار** — rolls, lots, locations, reservations, movements, barcode/QR. Owns: Q-046, Q-047, Q-048, Q-049, Q-051, Q-052. / رول‌ها، بچ‌ها، موقعیت‌ها، رزرو، گردش، بارکد/QR.
- **Purchasing / خرید** — suppliers, RFQ, purchasing approval, material lead times, receiving. Owns: Q-004/036, Q-005/050, Q-028. / تأمین‌کنندگان، استعلام، تأیید خرید، زمان تدارک، دریافت.
- **Maintenance / نگهداری و تعمیرات** — preventive maintenance, breakdowns, spare parts, machine availability. Owns: Q-017. / نگهداری پیشگیرانه، خرابی، قطعات یدکی، دسترس‌پذیری ماشین.
- **Finance / مالی** — costing, accounting boundaries, customer credit, receivables/payables, profitability. Owns: Q-031, Q-032, Q-033, Q-034, Q-035, Q-038. / بهای تمام‌شده، مرز حسابداری، اعتبار مشتری، دریافتنی/پرداختنی، سودآوری.

---

## E. Workshop Exit Criteria / خروجی مورد انتظار جلسه

> The workshop should end with an explicit decision (or a named owner + due date) on **each** of the 20 items below. / جلسه باید با تصمیم صریح (یا تعیین مسئول و مهلت) دربارهٔ **هر** ۲۰ مورد زیر پایان یابد.

| # | Item / موضوع | Decision required / تصمیم لازم | Suggested owner / مسئول پیشنهادی | Required output / خروجی لازم |
|---|--------------|-------------------------------|-----------------------------------|------------------------------|
| 1 | Product/spec model / مدل محصول و مشخصات | Confirm layered versioned model & code scheme | Engineering + Sales | Approved product-identity rule (Q-019, Q-024) |
| 2 | New vs repeat order / سفارش جدید در برابر تکراری | Define the two workflows & branch point | Sales | Two documented flows (Q-002) |
| 3 | Sampling / first article / نمونه و سری اول | When is sign-off mandatory? | Sales + Quality | Sampling policy (Q-003) |
| 4 | Artwork approval / تأیید آرت‌ورک | Internal + customer approval steps | Prepress + Sales | Approval sequence (Q-025) |
| 5 | Tooling management / مدیریت کلیشه | In-house/outsourced; who pays; amortize? | Prepress + Finance | Tooling policy (Q-004/036) |
| 6 | BOM structure / ساختار BOM | Levels + consumption basis + waste | Engineering | BOM standard (Q-026, Q-027) |
| 7 | Routing structure / ساختار مسیر | Templates per product group | Planning + Production | Routing standard (Q-029) |
| 8 | Production order lifecycle / چرخهٔ سفارش تولید | Confirm states & who releases/holds | Production | Approved state machine (Q-009) |
| 9 | Scheduling rules / قواعد زمان‌بندی | Priorities, capacity, alt machines | Planning | Scheduling policy (Q-011/015, Q-018) |
| 10 | Roll/lot tracking / ردیابی رول و بچ | Serialize? granularity? | Warehouse + Production | Tracking policy (Q-046, Q-049) |
| 11 | Quality checkpoints / نقاط کنترل کیفیت | Points, methods, sampling | Quality | Inspection plan (Q-039, Q-040) |
| 12 | Scrap/rework / ضایعات و دوباره‌کاری | Reason codes; reworkable vs scrap | Production + Quality | Scrap/rework policy (Q-016/042, Q-043) |
| 13 | Costing methodology / روش بهای تمام‌شده | Actual vs standard; valuation; rates | Finance | Costing method (Q-031, Q-033, Q-034) |
| 14 | Customer change orders / تغییر سفارش مشتری | How mid-order changes are handled | Sales | Change-order rule (Q-006 family) |
| 15 | Over/under delivery / تحویل کم/زیاد | Tolerance ± % and billing basis | Management + Sales | Tolerance policy (Q-006/037) |
| 16 | RMA / returns / مرجوعی | Return + complaint handling | Sales + Quality | RMA policy (A-006) |
| 17 | Approval hierarchy / سلسله‌مراتب تأیید | Thresholds & multi-step approvals | Management + Finance | Approval matrix (Q-054, Q-056) |
| 18 | User roles / نقش‌های کاربری | Confirm real org roles | Management | Role list (Q-053) |
| 19 | Required KPIs / شاخص‌های کلیدی | Which KPIs & profitability views | Management + Finance | KPI definitions (Q-038) |
| 20 | ERP/accounting boundary / مرز ERP و حسابداری | What integrates vs stays separate | Management + Finance | Integration boundary (Q-061) |

---

## F. Ground rules / قواعد پایه

**EN —** Nothing here is a confirmed SLZ rule until this workshop signs off. Recommendations are the software team's proposals, clearly labeled. History is never deleted; the software team will not code any decision marked OPEN. / **FA —** هیچ موردی تا تأیید این کارگاه، قاعدهٔ قطعی زرین نیست. پیشنهادها متعلق به تیم نرم‌افزار و مشخص‌شده‌اند. تاریخچه حذف نمی‌شود و تیم نرم‌افزار هیچ تصمیم «OPEN» را کدنویسی نخواهد کرد.

*Source: `docs/business-analysis/` (Task 001). Full detail per ID in `open-questions.md`. / منبع: مستندات فاز ۰۰۱.*

