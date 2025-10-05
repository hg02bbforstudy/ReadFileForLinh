// Final validation script for convert.html debugging
// Add this script to the page or run in console after file upload

function validateCVExtraction() {
    console.log('🔍 Running CV Extraction Validation...');
    
    // Check if we have access to the global variables
    if (typeof analyzeCVContent !== 'function') {
        console.log('❌ analyzeCVContent function not found');
        return;
    }
    
    // Hook into the file processing
    const originalAnalyze = analyzeCVContent;
    window.analyzeCVContent = function(text, htmlContent) {
        console.log('\n🎯 INTERCEPTING CV ANALYSIS');
        console.log(`Text length: ${text.length}`);
        
        // Run original analysis
        const result = originalAnalyze.call(this, text, htmlContent);
        
        // Validate results
        console.log('\n📊 VALIDATION RESULTS:');
        console.log('================================');
        
        // Check personal info
        const personal = result.personal;
        console.log('Personal Info:');
        console.log(`  Name: "${personal.name}" ${personal.name ? '✅' : '❌'}`);
        console.log(`  DOB: "${personal.dateOfBirth}" ${personal.dateOfBirth ? '✅' : '❌'}`);
        console.log(`  Gender: "${personal.gender}" ${personal.gender ? '✅' : '❌'}`);
        
        // Check contact info
        const contact = result.contact;
        console.log('\nContact Info:');
        console.log(`  Email: "${contact.email}" ${contact.email ? '✅' : '❌'}`);
        console.log(`  Phone: "${contact.phone}" ${contact.phone ? '✅' : '❌'}`);
        
        // Check education
        console.log(`\nEducation: ${result.education.length} entries ${result.education.length > 0 ? '✅' : '❌'}`);
        result.education.forEach((edu, idx) => {
            console.log(`  ${idx + 1}. ${typeof edu === 'object' ? edu.details : edu}`);
        });
        
        // Check experience - this is critical
        console.log(`\nExperience: ${result.experience.length} entries ${result.experience.length > 0 ? '✅' : '❌'}`);
        result.experience.forEach((exp, idx) => {
            if (typeof exp === 'object') {
                console.log(`  ${idx + 1}. ${exp.timeRange} - ${exp.position || exp.description} (Current: ${exp.isCurrent})`);
            } else {
                console.log(`  ${idx + 1}. ${exp}`);
            }
        });
        
        // Test the guess functions that were problematic
        console.log('\n🎯 TESTING EXTRACTION FUNCTIONS:');
        
        const currentPos = guessCurrentPosition(result);
        console.log(`Current Position: "${currentPos}" ${currentPos ? '✅' : '⚠️'}`);
        
        const experience = guessExperience(result);
        console.log(`Formatted Experience: ${experience ? '✅' : '❌'}`);
        if (experience) {
            const expLines = experience.split('\n');
            console.log(`  ${expLines.length} lines formatted`);
            expLines.forEach((line, idx) => {
                console.log(`    ${idx + 1}. ${line.substring(0, 80)}${line.length > 80 ? '...' : ''}`);
            });
        }
        
        const appliedPos = guessAppliedPosition(result);
        console.log(`Applied Position: "${appliedPos}" ${appliedPos ? '✅' : '⚠️'}`);
        
        console.log('\n📋 FINAL TABLE ROW DATA:');
        const tableRow = extractTableRow(result);
        Object.entries(tableRow).forEach(([key, value]) => {
            const status = value ? '✅' : (key === 'currentPosition' || key === 'appliedPosition' ? '⚠️' : '❌');
            console.log(`  ${key}: "${value}" ${status}`);
        });
        
        return result;
    };
    
    console.log('✅ Validation hook installed. Upload a file to test.');
}

// Auto-run validation setup
if (window.location.href.includes('convert.html')) {
    setTimeout(validateCVExtraction, 500);
}