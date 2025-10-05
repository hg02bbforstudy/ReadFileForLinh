// Test script to debug specific issues in convert.html
// Run this in the browser console when testing with the PDF file

console.log('🔍 Starting targeted debugging...');

// Test 1: Check if experience extraction is working
function testExperienceExtraction(text) {
    console.log('\n=== TEST 1: EXPERIENCE EXTRACTION ===');
    
    const experienceMatch = text.match(/QUÁ\s*TRÌNH\s*CÔNG\s*TÁC(.*?)(?=VỊ\s*TRÍ\s*ỨNG\s*TUYỂN|$)/is);
    
    if (!experienceMatch) {
        console.log('❌ PROBLEM: Could not find experience section');
        console.log('Looking for alternative patterns...');
        
        // Test different patterns
        const alternatives = [
            /kinh\s*nghiệm/i,
            /công\s*tác/i,
            /làm\s*việc/i
        ];
        
        alternatives.forEach((pattern, idx) => {
            if (pattern.test(text)) {
                console.log(`✓ Found alternative pattern ${idx + 1}: ${pattern}`);
            }
        });
        return null;
    }
    
    const experienceSection = experienceMatch[1].trim();
    console.log(`✅ Experience section found (${experienceSection.length} chars)`);
    console.log('First 200 chars:', experienceSection.substring(0, 200));
    
    return experienceSection;
}

// Test 2: Check experience parsing logic
function testExperienceParsing(experienceSection) {
    console.log('\n=== TEST 2: EXPERIENCE PARSING ===');
    
    const lines = experienceSection.split('\n').filter(line => line.trim());
    console.log(`Found ${lines.length} lines in experience section`);
    
    const experiences = [];
    
    lines.forEach((line, idx) => {
        console.log(`Line ${idx}: "${line}"`);
        
        // Test the regex pattern
        const expMatch = line.match(/(\d{1,2}\/20\d{2})\s*-\s*(\d{1,2}\/20\d{2}|nay|hiện tại)[:\s]*(.+)/i);
        
        if (expMatch) {
            const timeRange = `${expMatch[1]} - ${expMatch[2]}`;
            const description = expMatch[3].trim();
            const isCurrent = /nay|hiện tại/i.test(expMatch[2]);
            
            const exp = {
                timeRange,
                description,
                isCurrent,
                position: description.split('-')[0]?.trim(),
                company: description.split('-')[1]?.trim()
            };
            
            experiences.push(exp);
            
            console.log(`  ✅ MATCH: ${timeRange} | ${description} | Current: ${isCurrent}`);
            console.log(`    Position: "${exp.position}" | Company: "${exp.company}"`);
        } else {
            console.log(`  ❌ NO MATCH: Line doesn't match experience pattern`);
        }
    });
    
    return experiences;
}

// Test 3: Check current position logic
function testCurrentPositionLogic(experiences) {
    console.log('\n=== TEST 3: CURRENT POSITION LOGIC ===');
    
    if (!experiences || experiences.length === 0) {
        console.log('❌ No experiences to test');
        return '';
    }
    
    console.log(`Testing ${experiences.length} experience entries:`);
    
    experiences.forEach((exp, idx) => {
        console.log(`Experience ${idx + 1}:`);
        console.log(`  Time: ${exp.timeRange}`);
        console.log(`  isCurrent: ${exp.isCurrent} (${typeof exp.isCurrent})`);
        console.log(`  Position: "${exp.position}"`);
    });
    
    // Sort by time (latest first)
    const sorted = experiences.slice().sort((a, b) => {
        const getTime = (exp) => {
            const match = exp.timeRange.match(/(\d{1,2})\/(\d{4})/);
            return match ? parseInt(match[2]) * 12 + parseInt(match[1]) : 0;
        };
        return getTime(b) - getTime(a);
    });
    
    console.log('\nSorted experiences (newest first):');
    sorted.forEach((exp, idx) => {
        console.log(`  ${idx + 1}. ${exp.timeRange} - Current: ${exp.isCurrent}`);
    });
    
    const latestJob = sorted[0];
    if (latestJob && latestJob.isCurrent === true) {
        console.log(`✅ CURRENT POSITION FOUND: "${latestJob.position}"`);
        return latestJob.position;
    } else {
        console.log(`❌ NO CURRENT POSITION: Latest job (${latestJob?.timeRange}) is not current`);
        return '';
    }
}

// Test 4: Check experience formatting
function testExperienceFormatting(experiences) {
    console.log('\n=== TEST 4: EXPERIENCE FORMATTING ===');
    
    if (!experiences || experiences.length === 0) {
        console.log('❌ No experiences to format');
        return '';
    }
    
    const formatted = experiences.map(exp => {
        const result = `${exp.timeRange}: ${exp.description}`;
        console.log(`  Formatted: "${result}"`);
        return result;
    }).join('\n');
    
    console.log(`\n✅ FINAL FORMATTED EXPERIENCE (${formatted.length} chars):`);
    console.log(formatted);
    
    return formatted;
}

// Test 5: Check applied position extraction
function testAppliedPositionExtraction(text) {
    console.log('\n=== TEST 5: APPLIED POSITION EXTRACTION ===');
    
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    
    // Find the line containing "vị trí ứng tuyển"
    let appliedSectionLine = -1;
    for (let i = 0; i < lines.length; i++) {
        if (/vị\s*trí\s*ứng\s*tuyển/i.test(lines[i])) {
            appliedSectionLine = i;
            console.log(`✅ Found "vị trí ứng tuyển" at line ${i}: "${lines[i]}"`);
            break;
        }
    }
    
    if (appliedSectionLine === -1) {
        console.log('❌ PROBLEM: "vị trí ứng tuyển" section not found');
        return '';
    }
    
    // Extract positions from following lines
    const positions = [];
    for (let i = appliedSectionLine + 1; i < Math.min(appliedSectionLine + 10, lines.length); i++) {
        const line = lines[i];
        console.log(`Checking line ${i}: "${line}"`);
        
        // Check for numbered positions
        const numberedMatch = line.match(/^(\d+)\.\s*(.+)$/);
        if (numberedMatch) {
            const position = `${numberedMatch[1]}. ${numberedMatch[2].trim()}`;
            positions.push(position);
            console.log(`  ✅ Found numbered position: "${position}"`);
        } else if (line.length > 2 && !/^(thông tin|skills|education)/i.test(line)) {
            positions.push(line);
            console.log(`  ✅ Found position: "${line}"`);
        } else {
            console.log(`  ⚠️  Skipped: Too short or next section`);
        }
    }
    
    const result = positions.join(' ');
    console.log(`\n✅ APPLIED POSITIONS RESULT: "${result}"`);
    return result;
}

// Main test function
function runCompleteDebugTest() {
    console.log('🚀 Running complete debug test...');
    
    // Get the raw text (assuming it's available in window or as a parameter)
    const text = window.lastExtractedText || prompt('Paste the extracted CV text here for debugging:');
    
    if (!text) {
        console.log('❌ No text available for testing');
        return;
    }
    
    console.log(`📄 Testing with text (${text.length} characters)`);
    
    // Run all tests
    const experienceSection = testExperienceExtraction(text);
    const experiences = experienceSection ? testExperienceParsing(experienceSection) : [];
    const currentPosition = testCurrentPositionLogic(experiences);
    const formattedExperience = testExperienceFormatting(experiences);
    const appliedPosition = testAppliedPositionExtraction(text);
    
    // Summary
    console.log('\n🎯 DEBUGGING SUMMARY:');
    console.log('==================');
    console.log(`Current Position: "${currentPosition}" ${currentPosition ? '✅' : '❌'}`);
    console.log(`Experience Format: ${formattedExperience ? '✅' : '❌'} (${formattedExperience.split('\n').length} entries)`);
    console.log(`Applied Position: "${appliedPosition}" ${appliedPosition ? '✅' : '❌'}`);
    
    return {
        currentPosition,
        formattedExperience,
        appliedPosition,
        experiences
    };
}

// Auto-run if we can detect the convert.html page
if (window.location.href.includes('convert.html')) {
    console.log('🔍 Auto-running debug test on convert.html page...');
    setTimeout(runCompleteDebugTest, 1000);
} else {
    console.log('💡 To run debug test, call: runCompleteDebugTest()');
}