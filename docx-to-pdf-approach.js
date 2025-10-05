// DOCX to PDF conversion approach (requires external service)

async function convertDocxToPdfAndExtract(file) {
    try {
        // Option A: Use CloudConvert API (free tier available)
        const convertedPdf = await convertWithCloudConvert(file);
        
        // Option B: Use PDF-lib + docx-preview to render DOCX as HTML then PDF
        const convertedPdf2 = await convertWithDocxPreview(file);
        
        // Extract from converted PDF
        return await extractTextFromPDF(convertedPdf);
        
    } catch (error) {
        console.error('DOCX to PDF conversion failed:', error);
        // Fallback to direct DOCX parsing
        return await extractTextFromDOCX(file);
    }
}

// Method A: CloudConvert (requires API key)
async function convertWithCloudConvert(file) {
    const apiKey = 'YOUR_CLOUDCONVERT_API_KEY'; // Need to register
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('outputformat', 'pdf');
    
    const response = await fetch('https://api.cloudconvert.com/v2/convert/docx/pdf', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`
        },
        body: formData
    });
    
    if (response.ok) {
        return await response.blob();
    }
    throw new Error('CloudConvert failed');
}

// Method B: Client-side rendering approach
async function convertWithDocxPreview(file) {
    // Use docx-preview to render DOCX as HTML
    const arrayBuffer = await file.arrayBuffer();
    const htmlContent = await docx.renderAsync(arrayBuffer, document.createElement('div'));
    
    // Convert HTML to PDF using jsPDF or similar
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();
    
    // This is complex and may not preserve checkboxes well
    pdf.html(htmlContent, {
        callback: function (pdf) {
            return new Blob([pdf.output('arraybuffer')], { type: 'application/pdf' });
        }
    });
}

// Usage in main flow
async function processDocxFile(file) {
    console.log('Trying DOCX → PDF → Extract approach...');
    
    try {
        // Try conversion approach first
        const pdfResult = await convertDocxToPdfAndExtract(file);
        if (pdfResult && pdfResult.gender) {
            console.log('✓ Gender extracted via PDF conversion:', pdfResult.gender);
            return pdfResult;
        }
    } catch (error) {
        console.log('PDF conversion failed, using direct DOCX parsing');
    }
    
    // Fallback to improved DOCX parsing
    return await extractTextFromDOCX(file);
}