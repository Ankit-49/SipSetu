import fs from 'fs';
import path from 'path';

function walkDir(dir, callback) {
  fs.readdirSync(dir).forEach(f => {
    let dirPath = path.join(dir, f);
    let isDirectory = fs.statSync(dirPath).isDirectory();
    isDirectory ? walkDir(dirPath, callback) : callback(path.join(dir, f));
  });
}

walkDir('./src', function(filePath) {
  if (filePath.endsWith('.tsx') || filePath.endsWith('.ts')) {
    let content = fs.readFileSync(filePath, 'utf8');
    let changed = false;

    if (content.includes('from "wouter"')) {
      content = content.replace(/from "wouter"/g, 'from "react-router"');
      changed = true;
    }
    
    // Fix erroneous useState import
    if (content.includes('import { useState } from "react-router";')) {
        content = content.replace('import { useState } from "react-router";', 'import { useState } from "react";');
        changed = true;
    }
    
    // Replace href= with to= for Link components
    // A bit hacky but works for the standard <Link href="..."> pattern
    if (changed) {
        content = content.replace(/<Link([^>]*?)href=(['"{])/g, '<Link$1to=$2');
    }

    if (changed) {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log('Updated', filePath);
    }
  }
});
