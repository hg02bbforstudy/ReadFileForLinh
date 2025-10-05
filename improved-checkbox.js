// Improved DOCX checkbox detection strategies

// Strategy 1: Form field parsing
async function parseDocxFormFields(arrayBuffer) {
    const zip = await JSZip.loadAsync(arrayBuffer);
    const documentXml = await zip.file("word/document.xml").async("text");
    
    // Look for form fields (fldChar elements)
    const formFieldMatches = documentXml.match(/<w:fldChar[^>]*w:fldCharType="begin"[^>]*>.*?<w:fldChar[^>]*w:fldCharType="end"[^>]*>/gs);
    
    if (formFieldMatches) {
        for (const field of formFieldMatches) {
            // Check if it's a checkbox field
            if (field.includes('FORMCHECKBOX') || field.includes('☑') || field.includes('☐')) {
                // Extract nearby text to determine gender
                const genderMatch = field.match(/(nam|nữ)/gi);
                if (genderMatch) {
                    return genderMatch[0];
                }
            }
        }
    }
    return null;
}

// Strategy 2: Content control parsing  
async function parseDocxContentControls(arrayBuffer) {
    const zip = await JSZip.loadAsync(arrayBuffer);
    const documentXml = await zip.file("word/document.xml").async("text");
    
    // Look for content controls (sdt elements)
    const controlMatches = documentXml.match(/<w:sdt[^>]*>.*?<\/w:sdt>/gs);
    
    if (controlMatches) {
        for (const control of controlMatches) {
            // Check for checkbox content controls
            if (control.includes('checkbox') || control.includes('checked')) {
                const genderMatch = control.match(/(nam|nữ)/gi);
                if (genderMatch) {
                    return genderMatch[0];
                }
            }
        }
    }
    return null;
}

// Strategy 3: Symbol font analysis (improved)
async function parseDocxSymbolFonts(arrayBuffer) {
    const zip = await JSZip.loadAsync(arrayBuffer);
    const documentXml = await zip.file("word/document.xml").async("text");
    
    // Enhanced symbol detection with better context analysis
    const symbolPattern = /<w:sym[^>]*w:font="Wingdings"[^>]*w:char="([^"]*)"[^>]*\/>/g;
    let match;
    const symbols = [];
    
    while ((match = symbolPattern.exec(documentXml)) !== null) {
        const charCode = match[1];
        const position = match.index;
        
        // Get larger context (500 chars before and after)
        const start = Math.max(0, position - 500);
        const end = Math.min(documentXml.length, position + 500);
        const context = documentXml.substring(start, end);
        
        // Extract all text from context
        const textNodes = context.match(/<w:t[^>]*>([^<]*)<\/w:t>/g) || [];
        const contextTexts = textNodes.map(t => t.replace(/<[^>]*>/g, '').trim()).filter(t => t);
        
        symbols.push({
            charCode,
            position,
            isChecked: charCode === 'F0FE', // ☑
            isEmpty: charCode === 'F0A8',   // ☐
            contextTexts,
            fullContext: contextTexts.join(' ')
        });
    }
    
    // Analyze symbols for gender selection
    for (const symbol of symbols) {
        if (symbol.isChecked) {
            const contextLower = symbol.fullContext.toLowerCase();
            
            // More sophisticated gender detection
            const hasGender = contextLower.includes('giới') || contextLower.includes('tính');
            const hasNam = contextLower.includes('nam');
            const hasNu = contextLower.includes('nữ');
            
            if (hasGender && (hasNam || hasNu)) {
                // Use position-based analysis
                const genderWords = [];
                if (hasNam) genderWords.push({word: 'Nam', pos: contextLower.indexOf('nam')});
                if (hasNu) genderWords.push({word: 'Nữ', pos: contextLower.indexOf('nữ')});
                
                // Find closest gender word to checkbox
                if (genderWords.length === 1) {
                    return genderWords[0].word;
                } else if (genderWords.length === 2) {
                    // Choose based on proximity or order
                    const contextMid = symbol.fullContext.length / 2;
                    const distances = genderWords.map(g => Math.abs(g.pos - contextMid));
                    const closestIndex = distances.indexOf(Math.min(...distances));
                    return genderWords[closestIndex].word;
                }
            }
        }
    }
    
    return null;
}