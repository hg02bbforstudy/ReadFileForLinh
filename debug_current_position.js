// Debug script cho "Vị trí hiện tại" - chạy trong Console của convert.html
console.log('🔍 DEBUGGING VỊ TRÍ HIỆN TẠI...');

// Override guessCurrentPosition để debug chi tiết hơn
const originalGuessCurrentPosition = window.guessCurrentPosition;
window.guessCurrentPosition = function(cvInfo) {
    console.log('\n🎯 === DEBUG VỊ TRÍ HIỆN TẠI ===');
    console.log('Input cvInfo.experience:', cvInfo.experience);
    
    if (!Array.isArray(cvInfo.experience) || cvInfo.experience.length === 0) {
        console.log('❌ NO EXPERIENCE DATA');
        return '';
    }
    
    console.log(`📊 Total experience entries: ${cvInfo.experience.length}`);
    
    // Debug từng experience entry
    cvInfo.experience.forEach((exp, idx) => {
        console.log(`\n📋 Experience ${idx + 1}:`);
        console.log('  - Type:', typeof exp);
        console.log('  - Raw object:', exp);
        
        if (typeof exp === 'object' && exp !== null) {
            console.log('  - timeRange:', exp.timeRange);
            console.log('  - position:', exp.position);  
            console.log('  - company:', exp.company);
            console.log('  - description:', exp.description);
            console.log('  - isCurrent:', exp.isCurrent, '(type:', typeof exp.isCurrent, ')');
            console.log('  - raw:', exp.raw);
        }
    });
    
    // Filter structured experiences
    let structuredExperiences = cvInfo.experience.filter(exp => 
        typeof exp === 'object' && exp !== null && exp.timeRange
    );
    
    console.log(`\n🔍 Filtered structured experiences: ${structuredExperiences.length}`);
    
    if (structuredExperiences.length === 0) {
        console.log('❌ NO STRUCTURED EXPERIENCES FOUND');
        return '';
    }
    
    // Sort by time
    console.log('\n⏰ SORTING BY TIME...');
    structuredExperiences.sort((a, b) => {
        const getStartTime = (exp) => {
            console.log(`  Parsing timeRange: "${exp.timeRange}"`);
            const match = exp.timeRange.match(/(\d{1,2})\/(\d{4})/);
            if (match) {
                const year = parseInt(match[2]);
                const month = parseInt(match[1]);
                const time = year * 12 + month;
                console.log(`    → ${year}/${month} = ${time}`);
                return time;
            } else {
                console.log(`    → PARSE FAILED`);
                return 0;
            }
        };
        
        const timeA = getStartTime(a);
        const timeB = getStartTime(b);
        console.log(`  Comparing: ${a.timeRange}(${timeA}) vs ${b.timeRange}(${timeB})`);
        return timeB - timeA; // Newer first
    });
    
    console.log('\n📅 SORTED EXPERIENCES:');
    structuredExperiences.forEach((exp, idx) => {
        console.log(`  ${idx + 1}. ${exp.timeRange} - ${exp.position || 'NO POSITION'} (isCurrent: ${exp.isCurrent})`);
    });
    
    // Check latest job
    const latestJob = structuredExperiences[0];
    console.log('\n🎯 LATEST JOB ANALYSIS:');
    console.log('  - timeRange:', latestJob?.timeRange);
    console.log('  - position:', latestJob?.position);
    console.log('  - company:', latestJob?.company);
    console.log('  - description:', latestJob?.description);
    console.log('  - isCurrent:', latestJob?.isCurrent, '(type:', typeof latestJob?.isCurrent, ')');
    console.log('  - isCurrent === true?', latestJob?.isCurrent === true);
    
    let currentPosition = '';
    
    if (latestJob && latestJob.isCurrent === true) {
        console.log('✅ LATEST JOB IS CURRENT!');
        
        // Extract position
        if (latestJob.position) {
            currentPosition = latestJob.position;
            console.log(`  → Using position field: "${currentPosition}"`);
        } else if (latestJob.description) {
            const parsed = latestJob.description.split('-')[0].trim();
            currentPosition = parsed;
            console.log(`  → Parsing from description: "${currentPosition}"`);
        }
        
        console.log(`  → FINAL CURRENT POSITION: "${currentPosition}"`);
    } else {
        console.log('❌ LATEST JOB IS NOT CURRENT');
        console.log('  → Reasons:');
        console.log('    - No latest job?', !latestJob);
        console.log('    - isCurrent not true?', latestJob?.isCurrent !== true);
        console.log('    - isCurrent value:', latestJob?.isCurrent);
        console.log('    - isCurrent type:', typeof latestJob?.isCurrent);
    }
    
    console.log(`\n🎉 FINAL RESULT: "${currentPosition}"`);
    return currentPosition;
};

// Test function để chạy với data hiện tại
window.testCurrentPosition = function() {
    if (window.currentCV) {
        console.log('🧪 Testing with currentCV data...');
        
        // Simulate cvInfo from currentCV
        const testCvInfo = {
            experience: [
                // Test data - thay thế bằng data thực tế
                {
                    timeRange: "01/2023 - nay",
                    position: "Marketing Manager", 
                    company: "ABC Company",
                    description: "Marketing Manager - ABC Company",
                    isCurrent: true,
                    raw: "01/2023 - nay: Marketing Manager - ABC Company"
                },
                {
                    timeRange: "06/2021 - 12/2022", 
                    position: "Marketing Executive",
                    company: "XYZ Corp",
                    description: "Marketing Executive - XYZ Corp",
                    isCurrent: false,
                    raw: "06/2021 - 12/2022: Marketing Executive - XYZ Corp"
                }
            ]
        };
        
        const result = window.guessCurrentPosition(testCvInfo);
        console.log('🎯 TEST RESULT:', result);
        
    } else {
        console.log('❌ No currentCV data available. Upload a file first.');
    }
};

// Hook vào analyze function để intercept data
const originalAnalyzeCVContent = window.analyzeCVContent;
window.analyzeCVContent = function(text, htmlContent) {
    console.log('🔄 INTERCEPTING CV ANALYSIS...');
    const result = originalAnalyzeCVContent.call(this, text, htmlContent);
    
    console.log('\n📊 CV ANALYSIS RESULT:');
    console.log('Experience data:', result.experience);
    
    // Test current position extraction
    console.log('\n🎯 TESTING CURRENT POSITION EXTRACTION:');
    const currentPos = window.guessCurrentPosition(result);
    console.log('Current position result:', currentPos);
    
    return result;
};

console.log('✅ Debug script loaded!');
console.log('📋 Available commands:');
console.log('  - testCurrentPosition() - Test with sample data');
console.log('  - Upload a file to see debug output');
console.log('  - Check console for detailed analysis');