from pathlib import Path
import re, json, wave, subprocess, shutil, os, math
from collections import Counter
import numpy as np

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'practice_pack'
AUDIO=ROOT/'audio'
ROOT.mkdir(parents=True,exist_ok=True); AUDIO.mkdir(exist_ok=True)

# Topic-level phrasing keeps terminology Australian while avoiding fake jurisdiction-specific legal advice.
T={
'Business':('a small-business adviser','小型企業顧問','the business online portal','商業網上平台','official business details must match the entity actually trading','正式商業資料要同實際經營嘅實體一致','business records','商業紀錄'),
'Consumer affairs':('a consumer information officer','消費者事務資訊主任','the trader’s customer portal','商戶客戶網上平台','consumer guarantees and contract terms can affect the available remedy','消費者保障同合約條款會影響可以要求嘅補救','purchase records','購買紀錄'),
'Employment':('a workplace relations adviser','僱傭關係顧問','the employee self-service portal','僱員自助網上平台','minimum entitlements can depend on the award, agreement and employment type','最低僱傭待遇可能視乎 award、協議同僱傭類別','employment records','僱傭紀錄'),
'Health':('a clinic administration officer','診所行政職員','the clinic patient portal','診所病人網上平台','Medicare arrangements and fees can vary by service and provider','Medicare 安排同收費會因服務同醫療提供者而有分別','health records','醫療紀錄'),
'Immigration and settlement':('a migration service officer','移民服務職員','your ImmiAccount','你嘅 ImmiAccount','visa status and conditions should be checked against the current electronic record','簽證狀況同條件應以目前電子紀錄為準','immigration records','移民紀錄'),
'Legal':('a community legal service officer','社區法律服務職員','the court or service online portal','法院或者服務機構網上平台','deadlines and formal directions must be followed unless they are officially changed','除非正式更改，否則限期同正式指示都要遵守','legal documents','法律文件'),
'Community':('a local council customer service officer','市議會客戶服務職員','the council online services portal','市議會網上服務平台','local services usually depend on the correct address, eligibility and booking details','本地服務通常視乎正確地址、資格同預約資料','council records','市議會紀錄'),
'Education':('a student services officer','學生服務職員','the student online portal','學生網上平台','enrolment, fees and study obligations depend on the course and cut-off dates','註冊、學費同學習責任會視乎課程同截止日期','student records','學生紀錄'),
'Financial':('a bank customer service officer','銀行客戶服務職員','secure online banking','安全網上銀行','transactions and account features must be checked against the specific product terms','交易同戶口功能要按實際產品條款核對','account records','戶口紀錄'),
'Housing':('a property management officer','物業管理職員','the tenancy online portal','租務網上平台','tenancy procedures depend on the state or territory and the agreement','租務程序會視乎所在州或領地同租約','tenancy records','租務紀錄'),
'Insurance':('an insurance claims officer','保險索償主任','the insurer claims portal','保險公司索償網上平台','cover depends on the policy wording, limits, exclusions and any applicable excess','保障視乎保單條款、上限、不保事項同適用自付額','claim records','索償紀錄'),
'Social services':('a Services Australia or community support officer','Services Australia 或社區支援職員','your linked myGov service','你已連結嘅 myGov 服務','eligibility and payment rates depend on your circumstances and the information on record','資格同付款金額會視乎你嘅情況同紀錄資料','claim records','申請紀錄'),
}

# Each seed: topic | title | issue EN | issue Cantonese | key Australian term EN | Cantonese study equivalent | factual detail EN | Cantonese | evidence EN | Cantonese
RAW=r'''Business|Applying for an ABN|a new sole-trader registration|新成立嘅獨資經營登記|Australian Business Number, or ABN|澳洲商業號碼，即係 ABN|trading is planned to start on 1 September|計劃九月一日開始營業|photo ID and tax details|有相身份證明同稅務資料
Business|Registering a business name|a proposed business name|擬登記嘅商業名稱|registered business name|註冊商業名稱|the proposed name is Harbour Home Repairs|擬用名稱係 Harbour Home Repairs|ABN details and contact information|ABN 資料同聯絡資料
Business|GST registration threshold|a GST registration question|GST 登記問題|Goods and Services Tax, or GST|商品及服務稅，即係 GST|projected annual turnover is $78,000|預計全年營業額係七萬八千澳元|sales records and current forecasts|銷售紀錄同現時預測
Business|Preparing a tax invoice|a customer invoice problem|客戶發票問題|tax invoice|稅務發票|the invoice total is $1,650 including GST|發票總額係一千六百五十澳元，已包括 GST|sale record and ABN details|銷售紀錄同 ABN 資料
Business|Lodging a BAS|a quarterly business activity statement|每季業務活動報表|Business Activity Statement, or BAS|業務活動報表，即係 BAS|the quarter ended on 30 June|該季度喺六月三十日完結|sales, GST and expense records|銷售、GST 同開支紀錄
Business|Changing to a company|a change from sole trader to company|由獨資經營轉做公司|proprietary limited company, or Pty Ltd|私人有限公司，即係 Pty Ltd|the company is due to start on 1 October|公司預計十月一日開始運作|company registration and banking details|公司註冊同銀行資料
Business|Market stall permit|a weekend market-stall application|週末市集攤位申請|temporary food stall permit|臨時食品攤位許可證|the first market is on 12 September|第一個市集係九月十二日|public-liability and food-safety details|公眾責任保險同食品安全資料
Business|Supplier credit terms|a supplier account application|供應商戶口申請|thirty-day trading terms|三十日商業付款期|the first order is worth $4,800|第一張訂單價值四千八百澳元|business references and bank details|商業推薦資料同銀行資料
Consumer affairs|Faulty refrigerator|a complaint about a faulty refrigerator|雪櫃故障投訴|consumer guarantee|消費者保障|the $1,899 refrigerator failed after six weeks|一千八百九十九澳元嘅雪櫃用咗六星期就壞|receipt, photos and service report|收據、相片同維修報告
Consumer affairs|Used-car dealer dispute|a used-car complaint|二手車商投訴|major failure|嚴重故障|the car cost $16,500 three weeks ago|架車三星期前買入，價錢一萬六千五百澳元|sale contract and repair invoice|買賣合約同維修發票
Consumer affairs|Online order not delivered|a missing online order|未收到嘅網購訂單|proof of purchase|購買證明|$420 was paid on 28 July|七月二十八日已付款四百二十澳元|order confirmation and payment record|訂單確認同付款紀錄
Consumer affairs|Gym cancellation|a gym membership cancellation|健身中心會籍取消|cancellation terms|取消條款|another $89 was debited yesterday|琴日又扣咗八十九澳元|membership contract and cancellation email|會籍合約同取消電郵
Consumer affairs|Mobile plan billing|a mobile-plan billing dispute|手機計劃賬單爭議|itemised bill|分項賬單|the disputed charge is $65 this month|今個月爭議收費係六十五澳元|contract summary and recent bills|合約摘要同最近賬單
Consumer affairs|Renovation quote dispute|a home-renovation bill|家居裝修賬單|written quote|書面報價|the quote was $9,500 but the invoice is $12,300|報價九千五百澳元，但發票係一萬二千三百澳元|quote, invoice and messages|報價、發票同訊息紀錄
Consumer affairs|Cancelled travel service|a refund for a cancelled tour|取消旅行團後嘅退款|refund entitlement|退款權益|a $1,200 deposit was paid|已付一千二百澳元訂金|booking terms and cancellation notice|預訂條款同取消通知
Consumer affairs|Electricity account dispute|an unusually high electricity bill|異常高嘅電費賬單|meter reading|電錶讀數|the quarterly bill is $740|今季賬單係七百四十澳元|bill and current meter photo|賬單同最新電錶相片
Employment|Casual loading missing|a casual pay-rate query|臨時僱員工資率查詢|casual loading|臨時僱員附加薪酬|the base rate shown is $25.40 an hour|顯示嘅基本時薪係二十五個四毫澳元|roster, contract and pay slip|更表、合約同糧單
Employment|Weekend penalty rates|weekend shift payments|週末更份薪酬|penalty rates|特別時段附加工資|fourteen weekend hours were worked last pay period|上一個出糧期做咗十四個週末鐘|time sheet, roster and pay slip|工時表、更表同糧單
Employment|Award classification|a job classification|職位分類|modern award classification|現代 award 職級分類|supervisor duties have been done for three months|已經做咗三個月主管職務|job description and recent rosters|職位說明同最近更表
Employment|Annual leave request|an annual-leave request|年假申請|annual leave balance|年假結餘|ten days were requested from 5 October|申請十月五日起放十日假|leave request and current balance|假期申請同現時結餘
Employment|Personal leave evidence|a recent sick-leave absence|最近病假缺勤|personal or sick leave|個人假或者病假|two shifts were missed this week|今個星期缺席咗兩更|medical certificate and leave form|醫生證明同請假表
Employment|Unpaid superannuation|missing super contributions|欠交退休金供款|superannuation guarantee contribution|法定退休金供款|the missing period is April to June|缺少嘅期間係四月至六月|pay slips and super-fund statement|糧單同退休金基金結單
Employment|Workplace injury report|a workplace injury|工傷|incident report|事故報告|a wrist was injured during Tuesday’s shift|星期二返工時整傷手腕|medical certificate and incident details|醫生證明同事故詳情
Employment|Unfair dismissal enquiry|a recent dismissal|最近被解僱|unfair dismissal application|不公平解僱申請|employment ended on 7 August|僱傭關係喺八月七日終止|termination letter and employment contract|解僱信同僱傭合約
Employment|Flexible work request|a flexible-work request|彈性工作申請|flexible working arrangement|彈性工作安排|the request is to finish at 4 pm three days a week|申請每星期三日下晝四點收工|written request and proposed roster|書面申請同建議更表
Employment|Starting a new job|new-job payroll paperwork|新工出糧文件|Tax File Number declaration|稅務檔案號碼申報|the first pay date is 28 August|第一次出糧日期係八月二十八日|TFN declaration and super choice form|TFN 申報同退休金選擇表
Health|GP bulk billing|a GP appointment fee|普通科醫生診症費|bulk billing|直接向 Medicare 收費|the clinic charges $78 with a Medicare rebate available|診所收七十八澳元，可以申請 Medicare 回贈|Medicare card and appointment confirmation|Medicare 卡同預約確認
Health|Specialist referral|a specialist referral|專科轉介|specialist referral|專科轉介信|the appointment is booked for 18 November|專科預約係十一月十八日|GP referral and specialist booking|家庭醫生轉介信同專科預約資料
Health|Pathology test|a pathology test request|病理化驗要求|out-of-pocket cost|自付費用|the blood test is booked for Monday morning|驗血預約係星期一朝早|request form and Medicare card|化驗申請表同 Medicare 卡
Health|PBS prescription|an expensive prescription medicine|昂貴處方藥|Pharmaceutical Benefits Scheme, or PBS|藥物福利計劃，即係 PBS|the prescription is for a three-month supply|處方係三個月份量|prescription and Medicare details|處方同 Medicare 資料
Health|Urgent care clinic|same-day medical-care options|即日醫療選擇|Medicare Urgent Care Clinic|Medicare 緊急護理診所|the symptoms are not life-threatening|症狀唔屬於危及生命|Medicare card and medication list|Medicare 卡同現用藥物清單
Health|Dental treatment quote|a dental treatment estimate|牙科治療報價|treatment plan|治療計劃|the proposed crown costs $1,850|建議牙冠治療收一千八百五十澳元|written quote and health-fund details|書面報價同醫療保險資料
Health|Physiotherapy sessions|a physiotherapy booking|物理治療預約|gap payment|差額自付費|each session is quoted at $110|每次治療報價一百一十澳元|referral and insurer details|轉介信同保險資料
Health|Mental health care plan|a counselling referral|心理輔導轉介|mental health treatment plan|心理健康治療計劃|the GP appointment is next Wednesday|家庭醫生預約係下星期三|Medicare card and referral letters|Medicare 卡同轉介信
Health|Hospital discharge follow-up|hospital discharge instructions|出院跟進指示|discharge summary|出院摘要|the follow-up appointment is in seven days|跟進預約係七日後|discharge summary and medication list|出院摘要同藥物清單
Health|Antenatal appointment|an antenatal clinic booking|產前診所預約|antenatal care|產前護理|the first hospital appointment is on 22 September|第一次醫院預約係九月二十二日|referral, Medicare card and scan reports|轉介信、Medicare 卡同超聲波報告
Immigration and settlement|Checking VEVO|a visa-status check|簽證狀況查核|Visa Entitlement Verification Online, or VEVO|網上簽證權益查核系統，即係 VEVO|the passport was renewed last month|上個月換咗新護照|passport and visa grant notice|護照同簽證批准通知
Immigration and settlement|Bridging Visa A|a bridging-visa status query|過橋簽證狀況查詢|Bridging Visa A|A 類過橋簽證|the current substantive visa expires on 30 September|現有實質簽證喺九月三十日到期|visa grant notices and passport|簽證批准通知同護照
Immigration and settlement|Bridging Visa B travel|proposed overseas travel|計劃出境旅行|Bridging Visa B|B 類過橋簽證|travel is planned for ten days in October|計劃十月份出境十日|travel dates, passport and visa notice|旅行日期、護照同簽證通知
Immigration and settlement|Visa condition enquiry|current visa conditions|現有簽證條件|visa condition|簽證條件|a new roster would add twelve work hours a week|新更表每星期會多十二個工作鐘|visa grant notice and proposed roster|簽證批准通知同建議更表
Immigration and settlement|Updating passport details|new passport details|新護照資料|ImmiAccount update|ImmiAccount 資料更新|the new passport was issued on 2 August|新護照喺八月二日簽發|new passport biodata page|新護照個人資料頁
Immigration and settlement|Citizenship appointment|a citizenship appointment|入籍預約|identity documents|身份證明文件|the appointment is at 9:30 am on 15 October|預約係十月十五日上午九點半|passport, photo ID and appointment letter|護照、有相身份證同預約信
Immigration and settlement|AMEP English classes|English-class options after settlement|定居後英文課程選擇|Adult Migrant English Program, or AMEP|成人移民英語計劃，即係 AMEP|Tuesday and Thursday evenings are available|星期二同星期四夜晚有時間|eligibility details and photo ID|資格資料同有相身份證
Immigration and settlement|Qualification recognition|an overseas qualification enquiry|海外學歷查詢|qualification assessment|學歷評估|the degree was completed in Hong Kong in 2022|二零二二年喺香港完成學位|a degree certificate and academic transcript|學位證書同成績表
Legal|Traffic fine court option|a traffic infringement notice|交通違規罰款通知|infringement notice|違規罰款通知|the notice requires action by 9 September|通知要求九月九日前處理|notice, licence details and photographs|通知、駕駛執照資料同相片
Legal|NSW AVO enquiry|an AVO matter in New South Wales|新州 AVO 個案|Apprehended Violence Order, or AVO|暴力禁制令，即係 AVO|the next Local Court date is 21 September|下一次地方法院日期係九月二十一日|court papers and interim order|法院文件同臨時命令
Legal|Bail reporting condition|bail reporting conditions|保釋報到條件|bail condition|保釋條件|reporting is required every Monday before 6 pm|逢星期一下午六點前要報到|bail undertaking and work roster|保釋文件同工作更表
Legal|Witness statement|a witness-statement appointment|錄取證人供詞預約|witness statement|證人供詞|the interview is booked for Thursday afternoon|會面安排喺星期四下晝|appointment letter and relevant messages|預約信同相關訊息
Legal|Family dispute mediation|a family dispute-resolution appointment|家庭爭議解決預約|family dispute resolution|家庭爭議解決|the mediation is scheduled for 6 October|調解安排喺十月六日|appointment letter and parenting proposals|預約信同育兒安排建議
Legal|Small civil claim|a small civil claim|小額民事索償|civil claim|民事索償|the amount in dispute is $3,200|爭議金額係三千二百澳元|bank transfers and written messages|銀行轉賬紀錄同書面訊息
Legal|Legal aid eligibility|a legal-aid enquiry|法律援助查詢|legal aid|法律援助|the court date is in three weeks|三個星期後要上庭|income evidence and court documents|收入證明同法院文件
Legal|Requesting an adjournment|an upcoming court hearing|即將進行嘅法院聆訊|adjournment|押後聆訊|the hearing is listed for 3 September|聆訊排期係九月三日|court notice and medical evidence|法院通知同醫療證明
Community|Hard-waste collection|a council hard-waste booking|市議會大型廢物收集預約|hard-waste collection|大型廢物收集|the booking is for 14 September|預約收集日期係九月十四日|booking confirmation and property address|預約確認同物業地址
Community|Library membership|public-library membership|公共圖書館會籍|library card|圖書證|books are needed this Saturday|今個星期六想借書|photo ID and digital proof of address|有相身份證同電子地址證明
Community|Community-centre course|a community-centre course booking|社區中心課程預約|concession fee|優惠收費|the eight-week course costs $96|八星期課程收費九十六澳元|booking email and concession evidence|預約電郵同優惠資格證明
Community|Resident parking permit|a resident parking permit|居民泊車許可證|resident parking permit|居民泊車許可證|the old permit expires on 31 August|舊許可證喺八月三十一日到期|licence, lease and vehicle registration|駕駛執照、租約同車輛登記資料
Community|Pet registration|a dog registration|狗隻登記|pet registration|寵物登記|the dog is microchipped and three years old|隻狗有晶片，而家三歲|microchip details and proof of address|晶片資料同地址證明
Community|Volunteering with children|a volunteer application|義工申請|Working with Children Check, or WWCC|兒童工作審查，即係 WWCC|the program begins on 19 September|個計劃喺九月十九日開始|identity documents and volunteer details|身份證明同義工資料
Community|Neighbourhood noise complaint|a neighbourhood noise complaint|鄰里噪音投訴|noise complaint|噪音投訴|the disturbance usually starts after 11 pm|滋擾通常夜晚十一點後開始|dates, times and diary notes|日期、時間同日誌紀錄
Community|Sports-ground booking|a community sports-ground booking|社區運動場預約|facility hire|場地租用|the event is for forty people on 26 September|活動係九月二十六日，大約四十人|booking form and public-liability details|預約表同公眾責任保險資料
Education|Primary-school enrolment|a child’s school enrolment|小朋友小學入學申請|local intake area|本地收生區|the family moved to the suburb last week|一家上星期搬到呢個區|proof of address and child records|地址證明同小朋友資料
Education|Parent-teacher meeting|a parent-teacher interview|家長教師面談|parent-teacher interview|家長教師面談|the appointment is at 4:20 pm next Tuesday|預約係下星期二下晝四點二十分|booking confirmation and student details|預約確認同學生資料
Education|School absence|a recent school absence|最近學校缺課|attendance record|出席紀錄|three days were missed because of illness|因病缺課三日|medical certificate and absence note|醫生證明同缺席通知
Education|Childcare enrolment|a childcare place|托兒學位|Child Care Subsidy, or CCS|托兒津貼，即係 CCS|care is needed from 7 September, four days a week|九月七日起每星期需要四日托兒|enrolment form and family details|入學表同家庭資料
Education|TAFE course enrolment|a TAFE course enrolment|TAFE 課程註冊|Vocational Education and Training, or VET|職業教育及培訓，即係 VET|classes begin on 6 October|課堂喺十月六日開始|ID, study records and enrolment offer|身份證、學習紀錄同取錄通知
Education|CSP and HECS-HELP|a university fee arrangement|大學學費安排|Commonwealth Supported Place, or CSP|聯邦資助學額，即係 CSP|the semester student contribution is $4,300|今個學期學生供款係四千三百澳元|offer letter and fee statement|取錄信同學費結單
Education|Census date withdrawal|a course withdrawal|退科問題|census date|學籍及費用責任截止日，即係 census date|the census date is 31 August|census date 係八月三十一日|enrolment record and withdrawal request|註冊紀錄同退科申請
Education|USI for training|a training enrolment|培訓註冊|Unique Student Identifier, or USI|唯一學生識別號碼，即係 USI|orientation is on 11 September|迎新安排喺九月十一日|photo ID and existing USI details|有相身份證同現有 USI 資料
Financial|Unauthorised card transaction|a disputed card transaction|有爭議嘅信用卡交易|unauthorised transaction|未經授權交易|the charge is $286.40 from last night|琴晚有一筆二百八十六個四毫澳元收費|statement and transaction screenshot|月結單同交易截圖
Financial|Direct debit cancellation|a direct debit cancellation|取消自動扣賬|direct debit|自動扣賬|the next $74 debit is due on Friday|下一筆七十四澳元扣款星期五到期|account statement and merchant notice|戶口結單同商戶通知
Financial|BPAY payment reference|a BPAY payment problem|BPAY 付款問題|BPAY customer reference number|BPAY 客戶參考號碼|$510 was paid yesterday afternoon|琴日下午付款五百一十澳元|payment receipt and bill|付款收據同賬單
Financial|Credit-card interest|a credit-card interest charge|信用卡利息收費|interest-free period|免息期|the statement shows $48.70 interest|月結單顯示四十八個七毫澳元利息|two statements and payment receipt|兩期月結單同付款收據
Financial|Mortgage offset account|a home-loan offset account|按揭對沖戶口|offset account|對沖戶口|the offset balance is about $35,000|對沖戶口大約有三萬五千澳元|loan statement and product details|按揭結單同產品資料
Financial|Home-loan redraw|a home-loan redraw request|按揭提取多還款項要求|redraw facility|提取多還款項功能|the requested redraw amount is $6,000|想提取嘅金額係六千澳元|loan account and redraw conditions|按揭戶口同提取條件
Financial|Financial hardship|loan repayment difficulty|貸款還款困難|financial hardship assistance|財務困難援助|the difficulty may last about three months|困難可能維持大約三個月|income details and current expenses|收入資料同現時開支
Financial|Tax return refund|a delayed tax refund|延遲退稅|income tax assessment|入息稅評稅通知|the expected refund is $1,340|預計退稅係一千三百四十澳元|notice of assessment and bank details|評稅通知同銀行資料
Housing|Rental application|a rental application|租屋申請|rental application|租屋申請|the weekly rent is $590 for a twelve-month lease|週租五百九十澳元，租期十二個月|employment evidence and rental references|工作證明同租屋推薦資料
Housing|Bond and condition report|move-in tenancy paperwork|入住租務文件|condition report|物業狀況報告|the bond is $2,360 and move-in is 1 September|按金二千三百六十澳元，九月一日入住|bond receipt, lease and condition report|按金收據、租約同物業狀況報告
Housing|Urgent repairs|an urgent repair request|緊急維修要求|urgent repair|緊急維修|there has been no hot water since last night|由琴晚開始一直冇熱水|photos and written repair request|相片同書面維修要求
Housing|Rent increase notice|a rent increase notice|加租通知|rent increase notice|加租通知|rent may rise from $540 to $610 a week on 20 October|十月二十日起週租可能由五百四十加到六百一十澳元|tenancy agreement and increase notice|租約同加租通知
Housing|Ending a tenancy|a notice to end a tenancy|終止租約通知|termination notice|終止租約通知|the proposed move-out date is 30 September|預計搬走日期係九月三十日|lease and proposed written notice|租約同準備發出嘅書面通知
Housing|Breaking a fixed-term lease|leaving a fixed-term lease early|提早離開定期租約|break lease|提前終止租約|four months remain on the fixed term|定期租約仲有四個月|lease and proposed move-out date|租約同預計搬走日期
Housing|Bond refund dispute|a bond refund dispute|按金退款爭議|bond claim|按金申索|the proposed cleaning deduction is $420|建議清潔扣款係四百二十澳元|condition reports, photos and cleaning receipt|狀況報告、相片同清潔收據
Housing|Routine inspection|a routine rental inspection|例行租屋檢查|entry notice|入屋通知|the inspection is booked for Tuesday at 10 am|檢查安排喺星期二朝早十點|inspection notice and work roster|檢查通知同工作更表
Housing|Shared utility bill|a shared electricity charge|分攤電費|utility apportionment|公用事業費用分攤|the requested contribution is $230|要求分攤二百三十澳元|bill copy and tenancy agreement|賬單副本同租約
Housing|NSW tenancy tribunal|a New South Wales tenancy dispute|新州租務爭議|NSW Civil and Administrative Tribunal, or NCAT|新州民事及行政審裁處，即係 NCAT|the first repair request was sent six weeks ago|第一次維修要求係六星期前發出|lease, repair requests and photos|租約、維修要求同相片
Insurance|Motor claim excess|a motor-insurance claim|汽車保險索償|policy excess|保單自付額|the quoted excess is $850|所列自付額係八百五十澳元|policy schedule and claim notice|保單資料表同索償通知
Insurance|Storm damage at home|a home-insurance claim after a storm|暴風雨後家居保險索償|make-safe work|防止損失擴大嘅緊急工程|the storm occurred on Saturday night|暴風雨喺星期六晚發生|photos, repair quote and claim number|相片、維修報價同索償編號
Insurance|Travel insurance claim|a travel-insurance claim|旅遊保險索償|covered event|受保事件|extra accommodation cost $680|額外住宿費係六百八十澳元|airline notice, receipts and itinerary|航空公司通知、收據同行程表
Insurance|Private health waiting period|private-health cover before treatment|治療前私人醫療保險保障|waiting period|等候期|the procedure is booked for 4 November|手術預約係十一月四日|policy details and hospital quote|保單資料同醫院報價
Insurance|Premium renewal|an insurance renewal premium|保險續保保費|insurance premium|保費|the annual premium rose from $1,240 to $1,520|全年保費由一千二百四十加到一千五百二十澳元|renewal notice and policy schedule|續保通知同保單資料表
Insurance|Contents theft claim|a contents-theft claim|家居財物盜竊索償|proof of ownership|物品擁有證明|the estimated loss is about $3,700|估計損失大約三千七百澳元|police event number, photos and bank records|警方事故編號、相片同銀行紀錄
Insurance|AFCA complaint|an unresolved insurance complaint|未解決嘅保險投訴|Australian Financial Complaints Authority, or AFCA|澳洲金融投訴局，即係 AFCA|the final response letter arrived on 8 August|最終回覆信喺八月八日收到|final response, policy and claim documents|最終回覆、保單同索償文件
Social services|JobSeeker reporting|JobSeeker income reporting|JobSeeker 收入申報|JobSeeker Payment|JobSeeker 求職者補助金|earnings were $620 before tax this reporting period|今個申報期稅前收入六百二十澳元|pay slip and reporting details|糧單同申報資料
Social services|Rent Assistance update|updated rent details|更新租金資料|Rent Assistance|租金援助|rent increased from $470 to $510 a week|週租由四百七十加到五百一十澳元|new lease or rent-increase notice|新租約或者加租通知
Social services|Child Care Subsidy hours|changed childcare use|托兒使用情況變更|Child Care Subsidy, or CCS|托兒津貼，即係 CCS|the child now attends care four days a week|小朋友而家每星期返四日托兒|childcare enrolment and activity details|托兒註冊同活動資料
Social services|Parenting Payment enquiry|a Parenting Payment enquiry|Parenting Payment 查詢|Parenting Payment|育兒補助金|the separation date was 2 August|分居日期係八月二日|identity, income and household details|身份、收入同家庭資料
Social services|Carer Payment enquiry|a carer-payment enquiry|照顧者補助查詢|Carer Payment|照顧者補助金|work has reduced to twelve hours a week|工作減到每星期十二個鐘|care details, income records and medical forms|照顧資料、收入紀錄同醫療表格
Social services|NDIS plan manager|an NDIS plan-management question|NDIS 計劃管理問題|plan manager|計劃管理人|the therapy invoice is $245|治療發票係二百四十五澳元|NDIS plan, service agreement and invoice|NDIS 計劃、服務協議同發票
Social services|Emergency relief referral|an emergency-relief request|緊急援助要求|emergency relief|緊急生活援助|the next income payment is due in five days|下一筆收入五日後先收到|photo ID and current financial information|有相身份證同現時財務資料'''

S=[]
for line in RAW.splitlines():
    p=line.split('|')
    assert len(p)==10,(len(p),line)
    S.append(dict(topic=p[0],title=p[1],issue_en=p[2],issue_yue=p[3],term_en=p[4],term_yue=p[5],detail_en=p[6],detail_yue=p[7],doc_en=p[8],doc_yue=p[9]))
assert len(S)==100,len(S)

CONCERN={
'Business':('I may have to delay starting or running the business','可能要延遲開業或者營運'),
'Consumer affairs':('I may lose money or miss the chance to obtain a remedy','可能會有金錢損失，或者錯過要求補救嘅機會'),
'Employment':('my pay or employment entitlements may be recorded incorrectly','工資或者僱傭待遇可能記錄錯'),
'Health':('treatment may be delayed or I may face an unexpected cost','治療可能延誤，或者我要支付預料之外嘅費用'),
'Immigration and settlement':('I may misunderstand my current visa rights or conditions','可能誤解現有簽證權利或者條件'),
'Legal':('I may miss a deadline or accidentally breach a formal direction','可能錯過限期，或者無意中違反正式指示'),
'Community':('I may miss the booking or lose access to the service','可能錯過預約或者用唔到服務'),
'Education':('I may miss enrolment or become liable for an avoidable fee','可能錯過註冊，或者要承擔本來可以避免嘅費用'),
'Financial':('money may be lost or extra fees or interest may apply','可能有金錢損失，或者要畀額外費用同利息'),
'Housing':('I may pay extra rent or miss an important tenancy deadline','可能要多交租，或者錯過重要租務限期'),
'Insurance':('the claim may be delayed or part of the loss may not be paid','索償可能延誤，或者部分損失唔獲賠償'),
'Social services':('my payment or support may be delayed or calculated incorrectly','款項或者支援可能延誤，或者計算錯'),
}
ACTION={
'Business':('submit the correct application or update and keep the confirmation','提交正確申請或者更新資料，並保留確認紀錄'),
'Consumer affairs':('write to the trader, explain the problem and request an appropriate remedy','書面聯絡商戶，解釋問題同要求合適補救'),
'Employment':('ask payroll or the employer to review the matter in writing','以書面要求出糧部門或者僱主覆核'),
'Health':('ask the provider to confirm the booking, referral or fee in writing','要求醫療提供者以書面確認預約、轉介或者收費'),
'Immigration and settlement':('check the current official notice and update the relevant details online','查看最新正式通知，並喺網上更新相關資料'),
'Legal':('get advice promptly and respond through the correct legal process','盡快取得意見，並用正確法律程序回應'),
'Community':('submit the council booking or application with the requested information','連同所需資料提交市議會預約或者申請'),
'Education':('ask student services to check the enrolment, fee or course record','要求學生服務部核對註冊、學費或者課程紀錄'),
'Financial':('ask the bank to investigate the transaction or account setting','要求銀行調查交易或者戶口設定'),
'Housing':('write to the agent or rental provider and keep the tenancy evidence','書面聯絡地產代理或者出租方，並保留租務證據'),
'Insurance':('provide the available evidence and ask the insurer to review the claim','提供現有證據，並要求保險公司覆核索償'),
'Social services':('update the relevant details and provide the requested evidence','更新相關資料，並提供所要求嘅證明'),
}
DEAD=[('next Friday','下星期五'),('the end of this month','今個月底'),('the date shown on the notice','通知所列日期'),('the next scheduled appointment or payment','下一個已安排嘅預約或者付款日期')]
PROC=['five business days','seven to ten business days','two weeks','three to four weeks']
PROC_Y=['五個工作日','七至十個工作日','兩星期','三至四星期']

# Scenario-specific overrides prevent a broad-topic template from using the wrong Australian service context.
OV={
'Supplier credit terms':{
 'org':('a supplier accounts officer','供應商賬戶職員'),'portal':('the supplier account portal','供應商賬戶網上平台'),
 'rule':('commercial credit terms depend on the supplier’s account policy and credit approval','商業信貸付款期會視乎供應商嘅賬戶政策同信貸審批'),
 'records':('supplier account records','供應商賬戶紀錄'),'action':('complete the credit-account application and provide the requested business references','完成信貸戶口申請並提供所需商業推薦資料'),
 'interim':('confirm the payment terms for each order until credit approval is final','信貸正式批核之前，每張訂單都要確認付款條款'),
 'review':('ask the supplier accounts team to explain the credit decision or available payment terms','要求供應商賬戶部解釋信貸決定或者可用付款條款')},
'AMEP English classes':{
 'org':('a settlement-services officer','定居支援服務職員'),'portal':('the service enrolment portal','服務註冊網上平台'),
 'rule':('AMEP eligibility and class options depend on individual eligibility and available providers','AMEP 資格同上課選擇會視乎個人資格同可用課程提供者'),
 'records':('eligibility and enrolment records','資格同註冊紀錄'),'action':('ask for an AMEP eligibility assessment and suitable class options','查詢 AMEP 資格評估同合適上課選擇'),
 'interim':('keep your identity and eligibility documents ready for enrolment','準備好身份同資格文件，方便註冊'),
 'review':('ask the provider or settlement service to explain the available enrolment options','要求課程提供者或者定居服務解釋可用註冊選擇'),
 'concern':('I may miss an enrolment step or a suitable class option','可能錯過註冊程序或者合適課程選擇')},
'Qualification recognition':{
 'org':('a qualifications information officer','學歷資格資訊職員'),'portal':('the relevant assessing body’s online portal','相關評估機構嘅網上平台'),
 'rule':('the assessment pathway depends on the qualification, purpose and relevant assessing authority','評估途徑會視乎學歷、用途同相關評估機構'),
 'records':('qualification records','學歷紀錄'),'action':('identify the relevant assessing authority and submit the required qualification documents','搵出相關評估機構並提交所需學歷文件'),
 'interim':('keep original qualification documents and any required translations available','準備好學歷文件正本同任何所需翻譯'),
 'review':('ask the assessing body to explain its assessment or review process','要求評估機構解釋評估或者覆核程序'),
 'concern':('I may follow the wrong recognition pathway for work or study','可能用錯工作或者升學所需嘅學歷認可途徑'),
 'dead':('I submit my next employment or study application','我提交下一份工作或者升學申請'),
 'action_tail':('Keep the information factual and make sure names and dates match your records.','資料要按事實填寫，亦要確保姓名同日期同你嘅紀錄一致。')},
'Volunteering with children':{
 'org':('a volunteer screening officer','義工背景審查職員'),'portal':('the relevant state or territory screening portal','相關州或者領地嘅背景審查網上平台'),
 'rule':('screening requirements and the responsible authority depend on the state or territory and the role','審查要求同負責機構會視乎所在州或領地同義工職務'),
 'records':('screening and volunteer records','審查同義工紀錄'),'action':('apply for the required screening check using the correct jurisdictional process','用所在司法管轄區嘅正確程序申請所需背景審查'),
 'interim':('do not start restricted child-related duties until the organisation confirms the required clearance','機構確認所需審查完成之前，唔好開始受限制嘅兒童相關工作'),
 'review':('ask the screening authority or volunteer organisation to explain the application status','要求審查機構或者義工機構解釋申請狀況')},
'Primary-school enrolment':{
 'org':('a school administration officer','學校行政職員'),'portal':('the school enrolment portal','學校入學網上平台'),
 'rule':('enrolment requirements can depend on the school, local intake arrangements and supporting documents','入學要求可能視乎學校、本地收生安排同證明文件'),
 'records':('school enrolment records','學校入學紀錄'),'action':('complete the enrolment enquiry and provide the requested address and student documents','完成入學查詢並提供所需地址同學生文件'),
 'interim':('keep the school informed if the address or contact details change','如果地址或者聯絡資料有變，要通知學校'),
 'review':('ask the school to explain the enrolment decision or the relevant education-department pathway','要求學校解釋入學決定或者相關教育部門途徑')},
'Parent-teacher meeting':{
 'org':('a school administration officer','學校行政職員'),'portal':('the school booking portal','學校預約網上平台'),
 'rule':('meeting and interpreter arrangements depend on the school booking and available support','面談同傳譯安排會視乎學校預約同可用支援'),
 'records':('school booking records','學校預約紀錄'),'action':('confirm the meeting time and interpreter request with the school','同學校確認面談時間同傳譯員要求'),
 'interim':('keep the booking confirmation and tell the school promptly about any change','保留預約確認，如有變更盡快通知學校'),
 'review':('ask the school office to check the booking or support request','要求學校辦公室核對預約或者支援要求')},
'School absence':{
 'org':('a school administration officer','學校行政職員'),'portal':('the school parent portal','學校家長網上平台'),
 'rule':('attendance records depend on the absence information and evidence provided to the school','出席紀錄會視乎向學校提供嘅缺席資料同證明'),
 'records':('attendance records','出席紀錄'),'action':('send the absence explanation and supporting evidence to the school','向學校提交缺席解釋同證明'),
 'interim':('keep the school informed if the absence continues','如果繼續缺課，要通知學校'),
 'review':('ask the school to check or correct the attendance record','要求學校核對或者更正出席紀錄')},
'Childcare enrolment':{
 'org':('a childcare enrolment officer','托兒服務註冊職員'),'portal':('the childcare provider’s enrolment portal','托兒服務機構嘅註冊網上平台'),
 'rule':('provider enrolment and Child Care Subsidy details are related but administered through separate processes','托兒機構註冊同 Child Care Subsidy 資料有關連，但係分開處理嘅程序'),
 'records':('childcare enrolment records','托兒註冊紀錄'),'action':('complete the provider enrolment and check the family’s Child Care Subsidy details','完成托兒機構註冊並核對家庭嘅 Child Care Subsidy 資料'),
 'interim':('keep the provider updated about the child’s start date and attendance pattern','如開始日期或者出席安排有變，要通知托兒機構'),
 'review':('ask the provider about enrolment and Services Australia about subsidy-specific questions','入學問題向托兒機構查詢，津貼個別問題向 Services Australia 查詢')},
'Tax return refund':{
 'org':('an ATO service officer','澳洲稅務局服務職員'),'portal':('your myGov-linked ATO online service','你經 myGov 連結嘅 ATO 網上服務'),
 'rule':('tax-return and refund details should be checked against the ATO assessment and nominated payment information','報稅同退稅資料應按 ATO 評稅同已登記付款資料核對'),
 'records':('tax and payment records','稅務同付款紀錄'),'action':('check the notice of assessment and nominated bank details in the ATO-linked account','喺已連結 ATO 嘅帳戶核對評稅通知同登記銀行資料'),
 'interim':('keep the assessment notice and monitor official ATO messages','保留評稅通知並留意 ATO 正式訊息'),
 'review':('ask the ATO to explain the payment status or available review pathway','要求 ATO 解釋付款狀況或者可用覆核途徑')},
'NSW tenancy tribunal':{
 'org':('a New South Wales tenancy information officer','新南威爾士州租務資訊職員'),'portal':('the relevant NSW tenancy or tribunal online service','相關新州租務或者審裁網上服務'),
 'rule':('the appropriate NSW tenancy dispute pathway depends on the issue, evidence and procedural requirements','合適嘅新州租務爭議途徑會視乎問題、證據同程序要求'),
 'records':('tenancy dispute records','租務爭議紀錄'),'action':('organise the tenancy evidence and check the appropriate NSW dispute pathway','整理租務證據並核實合適嘅新州爭議處理途徑'),
 'interim':('keep paying undisputed rent and keep all repair correspondence','繼續交冇爭議嘅租金，並保留所有維修通訊'),
 'review':('ask the relevant tenancy service about the next step, including NCAT where appropriate','向相關租務服務查詢下一步，包括適用時嘅 NCAT 程序')},
'Private health waiting period':{
 'org':('a private health insurer member-services officer','私人醫療保險會員服務職員'),'portal':('the insurer’s member portal','保險公司會員網上平台'),
 'rule':('waiting periods and benefits depend on the policy, level of cover and treatment category','等候期同保障金額會視乎保單、保障級別同治療類別'),
 'records':('membership and benefit records','會員同保障紀錄'),'action':('ask the insurer to confirm in writing whether a waiting period applies to the planned treatment','要求保險公司書面確認計劃治療係咪適用等候期'),
 'interim':('keep the treatment booking and written cost estimate and do not assume the insurer will cover it','保留治療預約同書面費用估算，亦唔好自行假設保險一定賠'),
 'review':('use the insurer complaint process and ask about the appropriate external complaints body if unresolved','先用保險公司投訴程序，如未解決再查詢合適外部投訴機構')},
'AFCA complaint':{
 'org':('a financial complaints information officer','金融投訴資訊職員'),'portal':('the AFCA online complaint service','AFCA 網上投訴服務'),
 'rule':('AFCA eligibility depends on the complaint type, time limits and prior handling by the financial firm','AFCA 資格視乎投訴類別、時限同金融機構之前嘅處理'),
 'records':('complaint records','投訴紀錄'),'action':('prepare the final response and claim documents and check the AFCA complaint requirements','準備最終回覆同索償文件，並核實 AFCA 投訴要求'),
 'interim':('keep all correspondence and the financial firm’s final response','保留所有通訊同金融機構嘅最終回覆'),
 'review':('follow the complaint steps and information requested through the AFCA process','按 AFCA 程序所要求嘅投訴步驟同資料處理')},
'NDIS plan manager':{
 'org':('an NDIS plan-management officer','NDIS 計劃管理職員'),'portal':('the plan manager’s invoice portal','計劃管理人嘅發票網上平台'),
 'rule':('invoice handling depends on the participant’s plan-management arrangement, funding and service agreement','發票處理會視乎參加者嘅計劃管理安排、資金同服務協議'),
 'records':('NDIS plan and invoice records','NDIS 計劃同發票紀錄'),'action':('check the service agreement and send the invoice through the correct plan-management process','核對服務協議，並用正確計劃管理程序提交發票'),
 'interim':('keep the invoice and service-delivery evidence while payment is being checked','付款核對期間保留發票同服務提供證明'),
 'review':('ask the plan manager to explain the invoice decision and the next available dispute step','要求計劃管理人解釋發票決定同下一個可用爭議處理步驟')},
}

# Five semantic dialogue patterns reduce predictability while keeping the same exam-like constraints.
INTERIM={
'Business':('keep using only verified business details until any change is confirmed','任何更改確認之前只使用已核實嘅商業資料'),
'Consumer affairs':('keep the item, receipt and all written messages','保留貨品、收據同所有書面訊息'),
'Employment':('keep your rosters, time records and pay slips','保留更表、工時紀錄同糧單'),
'Health':('follow existing clinical advice and seek urgent help if symptoms worsen','照現有醫療建議做，如果症狀惡化就盡快求助'),
'Immigration and settlement':('do not assume new work or travel rights until the current conditions are checked','未核實現有條件之前，唔好自行假設有新嘅工作或者旅行權利'),
'Legal':('keep every notice and do not ignore any court or police direction','保留所有通知，亦唔好忽視任何法院或者警方指示'),
'Community':('keep your booking or request number','保留預約或者申請編號'),
'Education':('continue attending classes unless the provider tells you otherwise','除非院校另有通知，否則繼續上堂'),
'Financial':('monitor the account and keep all transaction records','留意戶口情況並保留所有交易紀錄'),
'Housing':('keep paying undisputed rent and keep written tenancy records','繼續交冇爭議嘅租金，並保留書面租務紀錄'),
'Insurance':('take reasonable steps to prevent further loss and keep evidence','採取合理措施防止損失擴大，並保留證據'),
'Social services':('report required changes and keep evidence of what you submit','按要求申報變更，並保留已提交資料嘅證明'),
}
REVIEW={
'Business':('ask the agency to check or correct the record in writing','要求相關部門以書面核對或者更正紀錄'),
'Consumer affairs':('write to the trader first, then contact the relevant state consumer service if needed','先書面聯絡商戶，有需要再聯絡所在州嘅消費者服務'),
'Employment':('raise it with the employer or payroll, then seek Fair Work information if needed','先向僱主或者出糧部門提出，有需要再向 Fair Work 查詢'),
'Health':('ask the practice manager or relevant health service to review the administrative issue','要求診所經理或者相關醫療服務覆核行政問題'),
'Immigration and settlement':('follow the contact or review pathway stated in the official notice','按正式通知所列嘅聯絡或者覆核途徑處理'),
'Legal':('get legal advice about the available review, legal-aid or court step','就可用嘅覆核、法律援助或者法院程序取得法律意見'),
'Community':('use the council complaint or written-review process','使用市議會投訴或者書面覆核程序'),
'Education':('use the education provider’s formal review or complaint process','使用院校嘅正式覆核或者投訴程序'),
'Financial':('use the bank’s internal dispute process, then AFCA if the matter is eligible','先用銀行內部爭議程序，如個案合資格再向 AFCA 跟進'),
'Housing':('use the relevant state tenancy service or tribunal process if needed','有需要時使用所在州嘅租務服務或者審裁程序'),
'Insurance':('use internal dispute resolution, then AFCA if the complaint is eligible','先用內部爭議處理程序，如投訴合資格再向 AFCA 跟進'),
'Social services':('ask for an explanation or formal review through the relevant service','經相關服務要求解釋或者正式覆核'),
}

def make_turns(s,i):
    org_en,org_yu,portal_en,portal_yu,rule_en,rule_yu,records_en,records_yu=T[s['topic']]
    concern_en,concern_yu=CONCERN[s['topic']]
    action_en,action_yu=ACTION[s['topic']]
    interim_en,interim_yu=INTERIM[s['topic']]
    review_en,review_yu=REVIEW[s['topic']]
    ov=OV.get(s['title'],{})
    org_en,org_yu=ov.get('org',(org_en,org_yu))
    portal_en,portal_yu=ov.get('portal',(portal_en,portal_yu))
    rule_en,rule_yu=ov.get('rule',(rule_en,rule_yu))
    records_en,records_yu=ov.get('records',(records_en,records_yu))
    action_en,action_yu=ov.get('action',(action_en,action_yu))
    interim_en,interim_yu=ov.get('interim',(interim_en,interim_yu))
    review_en,review_yu=ov.get('review',(review_en,review_yu))
    concern_en,concern_yu=ov.get('concern',(concern_en,concern_yu))
    dead_en,dead_yu=DEAD[i%len(DEAD)]
    dead_en,dead_yu=ov.get('dead',(dead_en,dead_yu))
    action_tail_en,action_tail_yu=ov.get('action_tail',('Keep the wording factual and include the relevant dates and amounts.','內容要按事實寫，並包括相關日期同金額。'))
    proc=PROC[i%len(PROC)]; proc_y=PROC_Y[i%len(PROC_Y)]
    proc_disp=f'about {proc}'
    proc_y_disp=f'大約{proc_y}'
    v=i%5

    if v==0:
        return [
        ('P',f"Good morning. You’re speaking with {org_en}. I’m calling about {s['issue_en']}. Please confirm your full name and reference number before we continue.",f"早晨。呢度係{org_yu}。我聯絡你係關於{s['issue_yue']}。繼續之前，請確認你嘅全名同參考編號。"),
        ('C',f"My concern is that {concern_en}. I’d like this resolved before {dead_en}.",f"我最擔心{concern_yu}。我想喺{dead_yu}之前處理好。"),
        ('P',f"The key term is {s['term_en']}. Generally, {rule_en}. We must check your exact facts.",f"關鍵用語係{s['term_yue']}。一般嚟講，{rule_yu}。我哋要核實你嘅實際資料。"),
        ('C',f"My paperwork says {s['detail_en']}. I wrote that down earlier, but I’m not sure it is still current. Could you check it?",f"我份文件寫住{s['detail_yue']}。呢個資料我之前記低咗，但唔肯定而家仲係咪最新。你可唔可以幫我核實？"),
        ('P',f"The record matches that detail. Next, {action_en}. Check every date and number before submitting.",f"紀錄同呢個細節一致。下一步係{action_yu}。提交之前要核對清楚每個日期同數字。"),
        ('C',f"I have {s['doc_en']}. One item is electronic. Do you need originals, or are clear uploaded copies acceptable?",f"我已經準備咗{s['doc_yue']}。其中一份係電子版本。你哋要正本，定係清晰上載副本都可以？"),
        ('P',f"Unless your notice says otherwise, use {portal_en}. Upload {s['doc_en']}, then save the receipt or reference.",f"除非通知另有指示，否則用{portal_yu}。上載{s['doc_yue']}，之後保存收據或者參考編號。"),
        ('C',f"How long should I wait? I’m worried that {concern_en}. Should I call again if I hear nothing tomorrow?",f"通常要等幾耐？我擔心{concern_yu}。如果聽日都冇消息，我係咪應該再打電話？"),
        ('P',f"Allow {proc_disp}. Meanwhile, {interim_en}. Don’t submit the same request twice unless asked.",f"預{proc_y_disp}。期間，{interim_yu}。除非有人要求，否則唔好重複提交同一要求。"),
        ('C',"If I disagree with the outcome, can I request a review or complain? Should I ask for written reasons first?","如果我唔同意結果，可唔可以要求覆核或者投訴？我係咪應該先要求書面理由？"),
        ('P',f"Ask for written reasons and keep a dated record. After that, {review_en}.",f"要求書面理由，並保留有日期嘅紀錄。之後，{review_yu}。"),
        ('C',f"Understood. I’ll follow that step and save the confirmation. I’ll note {s['term_en']} so I use the right wording next time.",f"明白。我會照做並保存確認紀錄。我亦會記低{s['term_yue']}，等下次用返正確講法。"),
        ]

    if v==1:
        return [
        ('P',f"Thanks for calling {org_en}. I can see an enquiry about {s['issue_en']}. First, please confirm your name and the reference on the record.",f"多謝你打嚟{org_yu}。我見到有一個關於{s['issue_yue']}嘅查詢。首先請確認姓名同紀錄上嘅參考編號。"),
        ('C',f"I received an update today. It mentions {s['term_en']}, and I’m not sure what that means for my situation.",f"我今日收到更新，入面提到{s['term_yue']}。我唔肯定呢個詞對我嘅情況有咩意思。"),
        ('P',f"That term matters because {rule_en}. Your current record also says {s['detail_en']}.",f"呢個詞重要，因為{rule_yu}。你目前紀錄亦顯示{s['detail_yue']}。"),
        ('C',f"So that detail still applies? I need to know before {dead_en}, because {concern_en}.",f"即係呢個細節仍然適用？我需要喺{dead_yu}之前知道，因為{concern_yu}。"),
        ('P',f"Yes, that is what the current record shows. If it is wrong or incomplete, {action_en}.",f"係，現有紀錄係咁顯示。如果資料錯誤或者唔完整，就要{action_yu}。"),
        ('C',f"I’ve gathered {s['doc_en']}. Which parts should I send, and can I submit them online rather than bring paper copies?",f"我已經準備咗{s['doc_yue']}。我要交邊部分？可唔可以網上提交，而唔使帶紙本？"),
        ('P',f"Use {portal_en} unless your notice gives another method. Upload readable copies and keep the submission reference.",f"除非通知列明另一種方法，否則用{portal_yu}。上載清晰副本，並保留提交參考編號。"),
        ('C',"If I submit everything today, what should I do while the matter is being assessed? I don’t want to accidentally make it worse.","如果我今日交齊資料，評估期間應該做啲咩？我唔想無意中令情況變差。"),
        ('P',f"The usual guide is {proc_disp}. While you wait, {interim_en}, and monitor any official messages.",f"一般參考時間係{proc_y_disp}。等候期間，{interim_yu}，並留意任何正式訊息。"),
        ('C',"If the final outcome is negative, can I ask the service to explain exactly why before I decide whether to challenge it?","如果最後結果對我不利，我可唔可以先要求機構清楚解釋原因，再決定係咪提出覆核？"),
        ('P',f"Yes. Ask for the decision and reasons in writing. If the issue remains unresolved, {review_en}.",f"可以。要求以書面提供決定同理由。如果問題仍然未解決，{review_yu}。"),
        ('C',f"All right. I’ll keep the documents together and use {s['term_en']} when I contact the service again.",f"好。我會將文件整理好，下次再聯絡服務機構時會用返{s['term_yue']}呢個詞。"),
        ]

    if v==2:
        return [
        ('P',f"I’m following up on {s['issue_en']}. Before we discuss the status, please confirm your full name and reference number for the file.",f"我係跟進{s['issue_yue']}。傾進度之前，請確認你嘅全名同檔案參考編號。"),
        ('C',f"Thanks. The detail I was given is that {s['detail_en']}. My concern is that {concern_en}.",f"多謝。我收到嘅資料係{s['detail_yue']}。我擔心{concern_yu}。"),
        ('P',f"Before deciding the next step, remember the term {s['term_en']}. In this type of matter, {rule_en}.",f"決定下一步之前，要記住{s['term_yue']}呢個詞。喺呢類事情，{rule_yu}。"),
        ('C',f"What could happen if I cannot get this sorted before {dead_en}? I don’t want to miss something important.",f"如果我喺{dead_yu}之前處理唔到，可能會點？我唔想錯過重要程序。"),
        ('P',f"Don’t assume the outcome. First, {action_en}. That gives the service the information needed to assess the matter.",f"唔好自行假設結果。首先，{action_yu}。咁樣服務機構先有需要嘅資料去評估。"),
        ('C',f"Will {s['doc_en']} be enough to start, or should I wait until I have every possible supporting document?",f"我有{s['doc_yue']}。呢啲夠唔夠開始處理，定係要等齊所有可能嘅證明先交？"),
        ('P',f"Start with the requested material through {portal_en}. An officer can ask for more information if something relevant is missing.",f"先經{portal_yu}提交已要求嘅資料。如果欠缺相關資料，職員可以再要求補充。"),
        ('C',"How will I know the documents were received? I want evidence of the date in case there is a deadline dispute later.","我點樣知道文件已經收到？我想保留日期證明，以防之後對限期有爭議。"),
        ('P',f"Save the electronic receipt or reference. Allow {proc_disp}; during that time, {interim_en}.",f"保存電子收據或者參考編號。預{proc_y_disp}；期間，{interim_yu}。"),
        ('C',"If nothing changes after that timeframe, should I lodge a new request, or should I ask for a status update on the existing one?","如果過咗呢個時間都冇變化，我應該重新申請，定係查詢現有申請嘅進度？"),
        ('P',f"Ask for a status update rather than duplicate the request. If you later dispute the outcome, {review_en}.",f"應該查詢進度，而唔係重複提交。如果之後對結果有爭議，{review_yu}。"),
        ('C',f"Understood. I’ll keep the reference and remember {s['term_en']}. That should help me explain the issue clearly.",f"明白。我會保留參考編號，亦會記住{s['term_yue']}。咁下次可以清楚解釋件事。"),
        ]

    if v==3:
        return [
        ('P',f"You asked us to explain {s['issue_en']}. I can do that after I confirm your full name and the reference number attached to the matter.",f"你之前要求我哋解釋{s['issue_yue']}。確認你嘅全名同相關參考編號之後，我可以同你講清楚。"),
        ('C',f"Yes. I can see that {s['detail_en']}, but I don’t understand how that affects what I should do next.",f"係。我見到{s['detail_yue']}，但唔明呢個細節會點影響我下一步要做嘅嘢。"),
        ('P',f"The key expression is {s['term_en']}. The important general point is that {rule_en}.",f"關鍵用語係{s['term_yue']}。一般最重要嘅一點係{rule_yu}。"),
        ('C',f"I need to deal with it before {dead_en}. Otherwise, I’m worried that {concern_en}.",f"我需要喺{dead_yu}之前處理。否則，我擔心{concern_yu}。"),
        ('P',f"The safest next step is to {action_en}. {action_tail_en}",f"最穩妥嘅下一步係{action_yu}。{action_tail_yu}"),
        ('C',f"I have {s['doc_en']}, but one date differs from an older record. Should I explain that difference when I submit the documents?",f"我有{s['doc_yue']}，但其中一個日期同舊紀錄唔同。提交文件時應唔應該解釋呢個差異？"),
        ('P',f"Yes. Upload the evidence through {portal_en} and briefly explain any genuine discrepancy. Keep the receipt or reference after submission.",f"應該。經{portal_yu}上載證明，並簡單解釋真實差異。提交後保留收據或者參考編號。"),
        ('C',"Could there be an extra fee or another consequence while the record is being checked? I want to plan for that possibility.","核對紀錄期間會唔會有額外費用或者其他後果？我想預先有準備。"),
        ('P',f"Timing depends on the service and record. Allow {proc_disp}. Meanwhile, {interim_en}.",f"時間要視乎實際服務同紀錄。預{proc_y_disp}。期間，{interim_yu}。"),
        ('C',"If the written decision still seems wrong, I want to challenge it properly rather than keep making phone calls. What should I do?","如果書面決定仍然似乎有錯，我想用正確程序處理，而唔係不停打電話。我應該點做？"),
        ('P',f"Keep the written decision and your evidence in date order. Then {review_en}.",f"將書面決定同證據按日期整理好。之後，{review_yu}。"),
        ('C',f"Thanks. I’ll do that and keep a note of {s['term_en']} with the reference number for future contact.",f"多謝。我會照做，亦會將{s['term_yue']}同參考編號一齊記低，方便之後聯絡。"),
        ]

    return [
        ('P',f"Let’s check the progress of {s['issue_en']}. For security, please confirm your full name and reference before I open the detailed record.",f"我哋睇下{s['issue_yue']}嘅進度。為保障資料安全，我打開詳細紀錄之前，請確認全名同參考編號。"),
        ('C',f"Earlier I was told {s['detail_en']}. I’m still concerned that {concern_en}.",f"之前有人話{s['detail_yue']}。我仍然擔心{concern_yu}。"),
        ('P',f"I can see that note. The key term on this file is {s['term_en']}. Remember that {rule_en}.",f"我見到嗰個紀錄。檔案上嘅關鍵用語係{s['term_yue']}。要留意{rule_yu}。"),
        ('C',f"Is anything else missing from my side? I’d rather provide it now than discover the problem after {dead_en}.",f"我呢邊仲欠唔欠資料？我寧願而家補交，都唔想過咗{dead_yu}先發現問題。"),
        ('P',f"The next step is to {action_en}. The service can then check whether anything further is required.",f"下一步係{action_yu}。之後服務機構可以再核對係咪仲需要其他資料。"),
        ('C',f"I have {s['doc_en']}. Can I upload those now, and will I receive something proving the time and date of submission?",f"我已經準備咗{s['doc_yue']}。我而家可唔可以上載？提交之後會唔會有證明顯示日期同時間？"),
        ('P',f"Yes. Use {portal_en}, then save the electronic receipt or reference. Check the uploaded files are readable before you finish.",f"可以。用{portal_yu}提交，之後保存電子收據或者參考編號。完成之前要檢查上載文件係咪清楚可讀。"),
        ('C',"Once I submit them, when should I follow up? I don’t want to phone too early, but I also don’t want to miss a response.","提交之後我應該幾時跟進？我唔想太早打電話，但亦唔想錯過回覆。"),
        ('P',f"Allow {proc_disp}. During that period, {interim_en}, and check the official contact channel regularly.",f"預{proc_y_disp}。期間，{interim_yu}，並定期查看正式聯絡渠道。"),
        ('C',"What if my address, phone number or another important detail changes before the service finishes assessing the matter?","如果評估完成之前，我嘅地址、電話或者其他重要資料有變，應該點做？"),
        ('P',f"Update any material change promptly and keep proof. If the final decision is disputed, {review_en}.",f"重要資料有變要盡快更新，並保留證明。如果對最終決定有爭議，{review_yu}。"),
        ('C',f"That makes sense. I’ll keep everything together and write down {s['term_en']} so I can refer to the matter accurately.",f"明白。我會將所有資料整理好，亦會記低{s['term_yue']}，等之後可以準確提及呢件事。"),
        ]

def wc(t): return len(re.findall(r"\b[\w’'-]+\b",t))

dialogues=[]
for i,s in enumerate(S,1):
    turns=make_turns(s,i-1)
    pro_lang='en' if i%2 else 'yue'
    segs=[]
    for n,(role,en,yu) in enumerate(turns,1):
        src_lang=pro_lang if role=='P' else ('yue' if pro_lang=='en' else 'en')
        source=en if src_lang=='en' else yu
        model=yu if src_lang=='en' else en
        segs.append(dict(n=n,role=role,source_lang=src_lang,source=source,model=model,en=en,yue=yu,wc=wc(en)))
    dialogues.append(dict(id=f'D{i:03d}',topic=s['topic'],title=s['title'],term=s['term_en'],term_yue=s['term_yue'],segments=segs,total=sum(x['wc'] for x in segs),maxseg=max(x['wc'] for x in segs)))

# Structural QA. NAATI cap is applied to the English/equivalent side here.
assert len(dialogues)==100
assert all(len(d['segments'])==12 for d in dialogues)
assert max(d['maxseg'] for d in dialogues)<=35,[(d['id'],d['maxseg']) for d in dialogues if d['maxseg']>35]

# ---------- Written resources ----------
(ROOT/'README_FIRST.md').write_text('''# NAATI CCL English–Cantonese: 100-Dialogue Practice Pack

This independent pack contains **100 original practice dialogues**, arranged as **50 two-dialogue mock tests**, covering all 12 broad CCL topic areas.

## How to use it

1. Choose a pair in `MOCK_TEST_PAIRINGS.md`.
2. Keep `SOURCE_SCRIPTS.md` and `MODEL_ANSWERS.md` closed.
3. Play the matching MP3 in `audio/`.
4. **Pause immediately after each chime**, interpret aloud into the other language, then resume.
5. Use first person, preserve every date/number/condition, and record yourself if possible.
6. Finish both dialogues before checking model renditions.
7. Review with `SELF_REVIEW_SHEET.md` and recycle missed terms aloud.

## Audio note

The MP3s are **real playable audio files generated with synthetic Australian-English and Cantonese voices**. They are not human/native recordings and are not a pronunciation authority. They are intended for listening, memory, terminology, direction-switching and exam-style practice.

## Files

- `STUDY_GUIDE.md`
- `DIALOGUE_INDEX.md`
- `MOCK_TEST_PAIRINGS.md`
- `SOURCE_SCRIPTS.md`
- `MODEL_ANSWERS.md`
- `AUSTRALIAN_TERMS_GLOSSARY.md`
- `NUMBERS_DATES_NOTE_TAKING_DRILLS.md`
- `SELF_REVIEW_SHEET.md`
- `AUDIO_MANIFEST.md`
- `audio/D001_....mp3` through `audio/D100_....mp3`

This is not an official NAATI product. Check current NAATI candidate instructions before the real test.
''',encoding='utf-8')

idx=['# Dialogue Index','','| ID | Topic | Scenario | Approx. equivalent words | Key term |','|---|---|---|---:|---|']
for d in dialogues: idx.append(f"| {d['id']} | {d['topic']} | {d['title']} | {d['total']} | {d['term']} |")
(ROOT/'DIALOGUE_INDEX.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')

pairs=['# 50 Mock-Test Pairings','','Complete both dialogues before checking answers.','']
for k in range(50):
    a,b=dialogues[k*2:k*2+2]
    pairs += [f"## Mock Test {k+1:02d}",f"- Dialogue 1: **{a['id']} — {a['title']}** ({a['topic']})",f"- Dialogue 2: **{b['id']} — {b['title']}** ({b['topic']})",'']
(ROOT/'MOCK_TEST_PAIRINGS.md').write_text('\n'.join(pairs),encoding='utf-8')

src=['# Source Scripts — Keep Closed During Blind Practice','','P = professional/service provider; C = client/community member.','']
ans=['# Model Interpretations','', '> These are suggested renditions, not the only acceptable wording. Preserve meaning, detail, register and natural target-language expression.','']
for d in dialogues:
    src += [f"## {d['id']} — {d['title']}",f"**Topic:** {d['topic']}  ",f"**Key term:** {d['term']} / {d['term_yue']}",'']
    ans += [f"## {d['id']} — {d['title']}",f"**Topic:** {d['topic']}",'']
    for x in d['segments']:
        lg='EN' if x['source_lang']=='en' else '粵'
        src += [f"**{x['n']:02d}. {lg} ({x['role']})** {x['source']}",'']
        dr='English → Cantonese' if x['source_lang']=='en' else 'Cantonese → English'
        ans += [f"**{x['n']:02d}. {dr}**",f"- Source: {x['source']}",f"- Model: {x['model']}",'']
(ROOT/'SOURCE_SCRIPTS.md').write_text('\n'.join(src),encoding='utf-8')
(ROOT/'MODEL_ANSWERS.md').write_text('\n'.join(ans),encoding='utf-8')

study='''# Study Guide — English ↔ Cantonese CCL

## 1. What to train

CCL is a short-consecutive interpreting test. Train four skills together: **meaning transfer**, **natural target language**, **short-term memory/notes**, and **controlled delivery**.

The current official format uses two recorded dialogues of about 300 words each. The speakers alternate English and the other language, individual segments are 35 words or fewer, and a chime signals when to interpret. Current published scoring requires at least 63/90 overall and at least 29/45 in each dialogue. Always check NAATI’s latest instructions before test day.

## 2. Listen for a message skeleton

Do not chase individual words. Capture:

**WHO → ISSUE → FACT → CONDITION → ACTION → DEADLINE / RESULT**

Example note:

`PM → rent ↑ 540→610 / 20 Oct / notice + lease / check rule`

At the chime, reconstruct the message naturally in the other language.

## 3. First-person interpreting

Keep the original speaker’s perspective:

- Source: “I need the receipt.” → `我需要張收據。`
- Source: `我下星期一先有時間。` → “I’m only available next Monday.”

Avoid “he says…” or `佢話…` unless those words are actually in the source.

## 4. Cantonese production

Aim for clear, neutral spoken Cantonese used in a service interaction.

Useful frames: `我想查詢…` · `我想確認…` · `你需要提供…` · `如果…就…` · `除非…否則…` · `有需要可以要求覆核…`

Do not force English word order into Cantonese. Keep common Australian program names/acronyms where natural—Medicare, Centrelink, myGov, NDIS, ABN, TFN, GST, HECS-HELP, VEVO—but understand what they mean so you can explain them.

## 5. English production

Preserve modality and logic exactly. **May, can, must, should, cannot** are different. So are **if, unless, until, before, only if**. Australian community English often uses `lodge`, `supporting evidence`, `eligible`, `rebate`, `excess`, `bond`, `award`, `concession`, `review`, `claim` and `notice`.

## 6. High-risk details

Always mark these in your notes: money, dates, times, ranges, changes, frequency, duration, negatives, comparisons, deadlines, conditions and official status.

Examples: `$540 → $610`; `31 Aug`; `before 6 pm`; `4 days/week`; `not eligible yet`; `unless evidence is provided`.

## 7. A compact note system

`↑` increase · `↓` decrease · `→` next/result · `≠` mismatch · `?` unclear · `DL` deadline · `doc` evidence · `wk/mo/yr` time · `b4/aft` before/after · `R` review · `C` complaint.

Use symbols consistently. Notes should trigger meaning, not become a transcript.

## 8. Review method

After every recorded attempt, ask:

1. Did I preserve the core proposition?
2. Were every number/date/name and condition exact?
3. What did I omit?
4. Did I add anything not said?
5. Did I strengthen, weaken or reverse meaning?
6. Was the target language natural and appropriate?
7. Did I pause, restart or self-correct too much?

Re-interpret failed segments after a short gap without memorising the model sentence.

## 9. Four-week plan

**Week 1 — accuracy:** 2 dialogues/day untimed; glossary + 10 minutes of number/date drills daily.  
**Week 2 — switching:** 3 dialogues/day; focus on Australian terminology and clean first-person delivery.  
**Week 3 — mock mode:** complete one two-dialogue mock on most days; record the whole attempt; review only after both dialogues.  
**Week 4 — exam discipline:** full mocks under current NAATI timing/repeat rules; paper notes only; start promptly; reduce notes to logic + high-risk detail.

## 10. Topic rotation

Practise all 12 areas: business, consumer affairs, employment, health, immigration/settlement, legal, community, education, financial, housing, insurance and social services.

## 11. Live practice with ChatGPT

Use a command such as: **“Test me on D037 in exam mode. Do not correct me until the end.”** For learning mode, ask for correction after each segment. Ask the marker to separate **meaning errors, missing details, language/register, delivery, and a stronger model rendition**.
'''
(ROOT/'STUDY_GUIDE.md').write_text(study,encoding='utf-8')

# Curated topic vocabulary: dialogue terms plus related Australian terms.
EXTRA={
'Business':['ABN|澳洲商業號碼','ACN|澳洲公司號碼','sole trader|獨資經營者','partnership|合夥企業','Pty Ltd|私人有限公司','GST|商品及服務稅','BAS|業務活動報表','tax invoice|稅務發票','turnover|營業額','supplier|供應商','trading terms|付款條款','public liability insurance|公眾責任保險'],
'Consumer affairs':['Australian Consumer Law|澳洲消費者法','consumer guarantee|消費者保障','major failure|嚴重故障','repair|維修','replacement|更換','refund|退款','proof of purchase|購買證明','written quote|書面報價','cooling-off period|冷靜期','cancellation terms|取消條款','itemised bill|分項賬單','remedy|補救'],
'Employment':['Fair Work Ombudsman|Fair Work 公平工作監察專員署','award|行業工資及僱傭條件規定','enterprise agreement|企業協議','casual loading|臨時僱員附加薪酬','penalty rates|特別時段附加工資','allowance|津貼','pay slip|糧單','roster|更表','annual leave|年假','personal leave|個人假','superannuation|退休金','TFN|稅務檔案號碼'],
'Health':['Medicare|Medicare 澳洲醫療保險制度','bulk billing|直接向 Medicare 收費','rebate|回贈','gap payment|差額自付費','GP|家庭醫生／普通科醫生','specialist|專科醫生','referral|轉介信','PBS|藥物福利計劃','prescription|處方','pathology|病理化驗','urgent care clinic|緊急護理診所','discharge summary|出院摘要'],
'Immigration and settlement':['Department of Home Affairs|內政部','ImmiAccount|ImmiAccount','VEVO|網上簽證權益查核系統','visa grant notice|簽證批准通知','visa condition|簽證條件','Bridging Visa A|A 類過橋簽證','Bridging Visa B|B 類過橋簽證','substantive visa|實質簽證','citizenship appointment|入籍預約','AMEP|成人移民英語計劃','settlement service|定居支援服務','qualification assessment|學歷評估'],
'Legal':['legal aid|法律援助','court notice|法院通知','hearing|聆訊','adjournment|押後聆訊','bail|保釋','bail condition|保釋條件','witness statement|證人供詞','AVO|暴力禁制令','interim order|臨時命令','mediation|調解','civil claim|民事索償','tribunal|審裁處'],
'Community':['local council|市議會','hard-waste collection|大型廢物收集','resident parking permit|居民泊車許可證','pet registration|寵物登記','microchip|晶片','library card|圖書證','community centre|社區中心','concession fee|優惠收費','Working with Children Check|兒童工作審查','volunteer|義工','noise complaint|噪音投訴','facility hire|場地租用'],
'Education':['enrolment|註冊／入學','local intake area|本地收生區','attendance|出席紀錄','Child Care Subsidy|托兒津貼','TAFE|TAFE 技術及持續教育院校','VET|職業教育及培訓','placement|實習','CSP|聯邦資助學額','HECS-HELP|HECS-HELP 學費貸款','census date|學籍及費用責任截止日','USI|唯一學生識別號碼','academic transcript|成績表'],
'Financial':['transaction account|交易戶口','direct debit|自動扣賬','BPAY|BPAY','EFTPOS|EFTPOS','unauthorised transaction|未經授權交易','interest-free period|免息期','home loan|按揭／房屋貸款','offset account|對沖戶口','redraw facility|提取多還款項功能','financial hardship|財務困難','ATO|澳洲稅務局','AFCA|澳洲金融投訴局'],
'Housing':['residential tenancy agreement|住宅租約','tenant / renter|租客','landlord / rental provider|業主／出租方','property manager|物業管理員／租務經理','rental bond|租屋按金','condition report|物業狀況報告','rent increase notice|加租通知','urgent repair|緊急維修','routine inspection|例行租屋檢查','entry notice|入屋通知','break lease|提前終止租約','NCAT|新州民事及行政審裁處'],
'Insurance':['premium|保費','policy|保單','policy schedule|保單資料表','PDS|產品披露聲明','excess|自付額','claim|索償','sum insured|保額','exclusion|不保事項','waiting period|等候期','proof of ownership|物品擁有證明','internal dispute resolution|內部爭議處理','AFCA|澳洲金融投訴局'],
'Social services':['Services Australia|Services Australia','Centrelink|Centrelink','myGov|myGov','CRN|客戶參考編號','JobSeeker Payment|JobSeeker 求職者補助金','Rent Assistance|租金援助','Child Care Subsidy|托兒津貼','Parenting Payment|育兒補助金','Carer Payment|照顧者補助金','NDIS|國家殘障保險計劃','plan manager|計劃管理人','support coordinator|支援協調員','service agreement|服務協議','emergency relief|緊急生活援助']}

g=['# Australian Terms Glossary','','These are study equivalents, not rigid one-to-one translations. Retain branded Australian names/acronyms where natural and interpret their meaning accurately.','']
for topic,arr in EXTRA.items():
    g += [f'## {topic}','','| Australian English | Cantonese study equivalent |','|---|---|']
    seen=set()
    # dialogue key terms first
    terms=[(d['term'],d['term_yue']) for d in dialogues if d['topic']==topic]
    terms += [tuple(x.split('|',1)) for x in arr]
    for en,yu in terms:
        if en.lower() in seen: continue
        seen.add(en.lower()); g.append(f'| {en} | {yu} |')
    g.append('')
(ROOT/'AUSTRALIAN_TERMS_GLOSSARY.md').write_text('\n'.join(g),encoding='utf-8')

(ROOT/'NUMBERS_DATES_NOTE_TAKING_DRILLS.md').write_text('''# Numbers, Dates and Note-Taking Drills

Interpret each item both ways without looking back.

## Money

- $89.50 — eighty-nine dollars and fifty cents — 八十九澳元五十仙
- $420 — four hundred and twenty dollars — 四百二十澳元
- $1,340 — one thousand three hundred and forty dollars — 一千三百四十澳元
- $1,899 — one thousand eight hundred and ninety-nine dollars — 一千八百九十九澳元
- $16,500 — sixteen thousand five hundred dollars — 一萬六千五百澳元
- $78,000 — seventy-eight thousand dollars — 七萬八千澳元
- $540 → $610/week — from $540 to $610 a week — 週租由五百四十加到六百一十澳元

## Dates and times

- 31 August — 八月三十一日
- 3 September — 九月三日
- 20 October — 十月二十日
- 18 November — 十一月十八日
- 9:30 am — 朝早九點半
- 4:20 pm — 下晝四點二十分
- before 6 pm every Monday — 逢星期一下午六點之前

## Contrast drill

Keep the difference exact: **can / must / may**; **before / after**; **at least / no more than**; **approved / pending / rejected**; **included / excluded**; **refundable / non-refundable**; **eligible / not eligible yet**; **if / unless**.

## 60-second note drill

Source: “The weekly rent will increase from $540 to $610 on 20 October. Please provide the written notice and your tenancy agreement before Friday so we can check the effective date.”

Try first. Suggested notes: `rent/wk 540→610 | 20/10 | doc notice+lease | b4 Fri | check start`.

Do five random source segments daily and write only logic + high-risk details.
''',encoding='utf-8')

(ROOT/'SELF_REVIEW_SHEET.md').write_text('''# Self-Review Sheet

**Dialogue:** ________  **Date:** ________  **Attempt:** 1 / 2 / 3

| Segment | Core meaning | Numbers/dates | Omission | Addition | Distortion | Natural language | Delivery issue |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
| 6 | | | | | | | |
| 7 | | | | | | | |
| 8 | | | | | | | |
| 9 | | | | | | | |
| 10 | | | | | | | |
| 11 | | | | | | | |
| 12 | | | | | | | |

**Three meaning errors not to repeat:** 1) ______ 2) ______ 3) ______  
**Five chunks/terms to recycle aloud:** ______________________________  
**Numbers/dates missed:** ___________________________________________  
**One delivery habit to fix:** ______________________________________

Re-attempt failed segments after a short gap. Do not simply memorise the model sentence.
''',encoding='utf-8')

(ROOT/'dialogues_metadata.json').write_text(json.dumps(dialogues,ensure_ascii=False,indent=2),encoding='utf-8')

print('TEXT_READY',len(dialogues),'MAX_SEG',max(d['maxseg'] for d in dialogues),'WORD_RANGE',min(d['total'] for d in dialogues),max(d['total'] for d in dialogues),flush=True)
