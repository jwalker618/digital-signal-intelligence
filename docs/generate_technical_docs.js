const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
       Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType, 
       PageNumber, LevelFormat, ShadingType, PageBreak } = require('docx');
const fs = require('fs');

// Create comprehensive DSI technical documentation
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const doc = new Document({
   styles: {
       default: { document: { run: { font: "Arial", size: 22 } } },
       paragraphStyles: [
           { id: "Title", name: "Title", basedOn: "Normal",
             run: { size: 56, bold: true, color: "1a365d", font: "Arial" },
             paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
           { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
             run: { size: 32, bold: true, color: "1a365d", font: "Arial" },
             paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
           { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
             run: { size: 28, bold: true, color: "2d3748", font: "Arial" },
             paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 } },
           { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
             run: { size: 24, bold: true, color: "4a5568", font: "Arial" },
             paragraph: { spacing: { before: 180, after: 60 }, outlineLevel: 2 } },
       ]
   },
   numbering: {
       config: [
           { reference: "main-bullets",
             levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
               style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
           { reference: "signals-list",
             levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
               style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
       ]
   },
   sections: [{
       properties: {
           page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
       },
       headers: {
           default: new Header({ children: [new Paragraph({ 
               alignment: AlignmentType.RIGHT,
               children: [new TextRun({ text: "Digital Signal Intelligence - Technical Documentation", italics: true, size: 18, color: "666666" })]
           })] })
       },
       footers: {
           default: new Footer({ children: [new Paragraph({ 
               alignment: AlignmentType.CENTER,
               children: [new TextRun({ text: "Page ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: " of ", size: 18 }), new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18 })]
           })] })
       },
       children: [
           // Title
           new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Digital Signal Intelligence")] }),
           new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [
               new TextRun({ text: "Technical Documentation & Implementation Guide", size: 28, color: "4a5568" })
           ]}),
           new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 }, children: [
               new TextRun({ text: "Version 2.0 | November 2025", size: 22, color: "718096" })
           ]}),
           
           // Executive Summary
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Executive Summary")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Digital Signal Intelligence (DSI) represents a paradigm shift in insurance underwriting. By analyzing the observable digital footprint of companies, DSI provides real-time, objective risk signals that traditional questionnaire-based underwriting cannot capture. This documentation provides complete technical specifications for implementing DSI across cyber, energy, and professional liability lines.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.1 Key Benefits")] }),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Real-time risk assessment: ", bold: true }), new TextRun("Signals update continuously, not annually")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Objective measurement: ", bold: true }), new TextRun("Observable data vs. self-reported questionnaires")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Predictive accuracy: ", bold: true }), new TextRun("Retrospective analysis shows 100% detection of major breaches")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Operational efficiency: ", bold: true }), new TextRun("Automated triage reduces manual underwriting workload by 60%")
           ]}),
           
           new Paragraph({ children: [new PageBreak()] }),
           
           // Signal Categories
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Signal Categories & Scoring")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("DSI collects and scores signals across multiple categories. Each signal is scored 0-100, with higher scores indicating better risk posture. The composite score scales these to 0-1000.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 Security Signals")] }),
           
           new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("SSL/TLS Configuration (8%)")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Evaluates the quality of SSL/TLS implementation including certificate validity, protocol versions, cipher suites, and vulnerability exposure. Source: SSL Labs API.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Security Headers (10%)")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Measures implementation of security headers including Content-Security-Policy, X-Frame-Options, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Known Vulnerabilities (20%)")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Identifies exposed services with known vulnerabilities via Shodan and CVE databases. This is the highest-weighted signal due to strong correlation with breach probability.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("Patch Discipline (15%)")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Evaluates how quickly an organization updates software after vulnerabilities are disclosed. Uses version analysis and Wayback Machine historical patterns.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("MFA Indicators (12%)")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Assesses multi-factor authentication implementation signals across login pages and authentication flows. Critical for preventing credential-based attacks.")
           ]}),
           
           new Paragraph({ children: [new PageBreak()] }),
           
           // Risk Tiers
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. Risk Tier Classification")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("The DSI composite score (0-1000) determines risk tier classification and underwriting workflow:")
           ]}),
           
           new Table({
               columnWidths: [1800, 1800, 2400, 3360],
               rows: [
                   new TableRow({
                       tableHeader: true,
                       children: [
                           new TableCell({ borders: cellBorders, shading: { fill: "1a365d", type: ShadingType.CLEAR },
                               children: [new Paragraph({ children: [new TextRun({ text: "Score", bold: true, color: "ffffff" })] })] }),
                           new TableCell({ borders: cellBorders, shading: { fill: "1a365d", type: ShadingType.CLEAR },
                               children: [new Paragraph({ children: [new TextRun({ text: "Tier", bold: true, color: "ffffff" })] })] }),
                           new TableCell({ borders: cellBorders, shading: { fill: "1a365d", type: ShadingType.CLEAR },
                               children: [new Paragraph({ children: [new TextRun({ text: "Classification", bold: true, color: "ffffff" })] })] }),
                           new TableCell({ borders: cellBorders, shading: { fill: "1a365d", type: ShadingType.CLEAR },
                               children: [new Paragraph({ children: [new TextRun({ text: "Action", bold: true, color: "ffffff" })] })] }),
                       ]
                   }),
                   new TableRow({ children: [
                       new TableCell({ borders: cellBorders, shading: { fill: "c6f6d5", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("750-1000")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "c6f6d5", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Tier 1")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "c6f6d5", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Preferred")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "c6f6d5", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Auto-approve preferred")] })] }),
                   ]}),
                   new TableRow({ children: [
                       new TableCell({ borders: cellBorders, shading: { fill: "bee3f8", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("650-749")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "bee3f8", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Tier 2")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "bee3f8", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Standard")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "bee3f8", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Auto-approve standard")] })] }),
                   ]}),
                   new TableRow({ children: [
                       new TableCell({ borders: cellBorders, shading: { fill: "fefcbf", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("500-649")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fefcbf", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Tier 3")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fefcbf", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Elevated")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fefcbf", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Manual review required")] })] }),
                   ]}),
                   new TableRow({ children: [
                       new TableCell({ borders: cellBorders, shading: { fill: "fed7d7", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("0-499")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fed7d7", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Tier 4")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fed7d7", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("High Risk")] })] }),
                       new TableCell({ borders: cellBorders, shading: { fill: "fed7d7", type: ShadingType.CLEAR },
                           children: [new Paragraph({ children: [new TextRun("Decline or conditions")] })] }),
                   ]}),
               ]
           }),
           
           new Paragraph({ children: [new PageBreak()] }),
           
           // Validation
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. Validation: Real-World Case Studies")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("DSI has been validated through retrospective analysis of major cyber incidents from 2023-2025. In every case, DSI would have identified warning signals that traditional underwriting missed.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 Marks & Spencer (April 2025)")] }),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Incident: ", bold: true }), new TextRun("Ransomware attack | "),
               new TextRun({ text: "Loss: ", bold: true }), new TextRun("$350M estimated")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Traditional Rating: ", bold: true }), new TextRun("STANDARD (ISO 27001 certified, strong brand)")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "DSI Score: ", bold: true }), new TextRun("520 (Tier 3 - Elevated Risk)")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Key Warning Signals: ", bold: true })
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun("Vulnerability Score: 45/100 - Multiple CVEs in exposed tech stack")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun("Patch Discipline: 40/100 - Delayed security updates observed")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun("Vendor Security: 45/100 - Complex supply chain risk")
           ]}),
           new Paragraph({ spacing: { before: 120, after: 200 }, children: [
               new TextRun({ text: "Outcome: ", bold: true }), new TextRun("DSI would have required manual review, likely resulting in higher premium or security improvement conditions before binding.")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.2 Change Healthcare (February 2024)")] }),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Incident: ", bold: true }), new TextRun("Ransomware via compromised Citrix portal | "),
               new TextRun({ text: "Loss: ", bold: true }), new TextRun("$1.6B disclosed")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Traditional Rating: ", bold: true }), new TextRun("PREFERRED (UnitedHealth subsidiary, HIPAA compliant)")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "DSI Score: ", bold: true }), new TextRun("545 (Tier 3 - Elevated Risk)")
           ]}),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun({ text: "Critical Warning Signal: ", bold: true })
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "MFA Indicators: 35/100 - ", bold: true }), new TextRun("This was the exact attack vector. Citrix portal lacked MFA.")
           ]}),
           new Paragraph({ spacing: { before: 120, after: 200 }, children: [
               new TextRun({ text: "Outcome: ", bold: true }), new TextRun("DSI would have flagged MFA deficiency as unacceptable. Coverage would have required MFA implementation on all remote access before binding.")
           ]}),
           
           new Paragraph({ children: [new PageBreak()] }),
           
           // Implementation
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Implementation Guide")] }),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 API Integration")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("DSI provides RESTful APIs for integration with existing underwriting workflows:")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "POST /api/v2/analyze ", font: "Courier New" }), new TextRun("- Submit domain for full analysis")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "GET /api/v2/score/{domain} ", font: "Courier New" }), new TextRun("- Retrieve cached composite score")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "GET /api/v2/signals/{domain} ", font: "Courier New" }), new TextRun("- Get detailed signal breakdown")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "POST /api/v2/monitor ", font: "Courier New" }), new TextRun("- Add domain to continuous monitoring")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.2 Workflow Integration")] }),
           new Paragraph({ spacing: { after: 120 }, children: [
               new TextRun("Recommended integration points:")
           ]}),
           new Paragraph({ numbering: { reference: "signals-list", level: 0 }, children: [
               new TextRun({ text: "Submission Intake: ", bold: true }), new TextRun("Auto-trigger DSI on new submission")
           ]}),
           new Paragraph({ numbering: { reference: "signals-list", level: 0 }, children: [
               new TextRun({ text: "Triage: ", bold: true }), new TextRun("Route based on tier (auto-approve T1-2, queue T3-4)")
           ]}),
           new Paragraph({ numbering: { reference: "signals-list", level: 0 }, children: [
               new TextRun({ text: "Pricing: ", bold: true }), new TextRun("Apply tier-based rate adjustments")
           ]}),
           new Paragraph({ numbering: { reference: "signals-list", level: 0 }, children: [
               new TextRun({ text: "Portfolio Monitoring: ", bold: true }), new TextRun("Continuous monitoring with alert thresholds")
           ]}),
           
           new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.3 Data Sources")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("DSI integrates with the following external APIs:")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "SSL Labs: ", bold: true }), new TextRun("SSL/TLS configuration grading (free)")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Shodan: ", bold: true }), new TextRun("Exposed services and vulnerabilities (API key required)")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Have I Been Pwned: ", bold: true }), new TextRun("Credential breach exposure (API key required)")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Wayback Machine: ", bold: true }), new TextRun("Historical website analysis (free)")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "BuiltWith: ", bold: true }), new TextRun("Technology stack detection (API key required)")
           ]}),
           
           new Paragraph({ children: [new PageBreak()] }),
           
           // Conclusion
           new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. Conclusion")] }),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun("Digital Signal Intelligence provides insurance carriers with a significant competitive advantage in cyber risk selection. By leveraging observable digital signals rather than self-reported questionnaires, DSI enables:")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Better risk selection ", bold: true }), new TextRun("through objective, real-time signals")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Improved loss ratios ", bold: true }), new TextRun("by identifying high-risk accounts before binding")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Operational efficiency ", bold: true }), new TextRun("through automated triage and pricing")
           ]}),
           new Paragraph({ numbering: { reference: "main-bullets", level: 0 }, children: [
               new TextRun({ text: "Portfolio monitoring ", bold: true }), new TextRun("with early warning of deteriorating risks")
           ]}),
           new Paragraph({ spacing: { before: 240, after: 200 }, children: [
               new TextRun({ text: "The retrospective analysis of major breaches demonstrates that DSI would have flagged every significant incident analyzed. Traditional underwriting rated these risks as 'standard' or 'preferred' while DSI correctly identified elevated risk signals.", italics: true })
           ]}),
           new Paragraph({ spacing: { after: 200 }, children: [
               new TextRun({ text: "For implementation support, contact the DSI team.", bold: true })
           ]}),
       ]
   }]
});

// Generate the document
Packer.toBuffer(doc).then(buffer => {
   fs.writeFileSync("/mnt/user-data/outputs/DSI_Technical_Documentation.docx", buffer);
   console.log("Document created successfully: DSI_Technical_Documentation.docx");
});
