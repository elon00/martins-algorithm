@echo off
echo ========================================
echo LUTHER'S GOLDEN ALGORITHM - GITHUB DEPLOYMENT
echo ========================================
echo.

echo Step 1: Please create GitHub repository first
echo - Go to: https://github.com/new
echo - Repository name: luthers-algorithm-framework
echo - Description: Enhanced NIST-approved post-quantum cryptography framework with advanced features
echo - UNCHECK "Add a README file"
echo - Click "Create repository"
echo.
pause

echo.
echo Step 2: Enter your GitHub username:
set /p username="GitHub Username: "

echo.
echo Connecting to GitHub repository...
git remote add origin https://github.com/%username%/luthers-algorithm-framework.git

echo.
echo Setting main branch...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Verify on GitHub:
echo - Check GitHub Actions CI/CD status
echo - Verify README displays correctly
echo - Confirm all files uploaded
echo.
echo Your Luther's Golden Algorithm is now live!
echo.
pause