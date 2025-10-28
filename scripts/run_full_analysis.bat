@echo off
REM ============================================================================
REM AF3 预测结果完整质量分析脚本 (Windows版本)
REM ============================================================================
REM 
REM 功能：
REM   1. 提取 pLDDT 值（局部结构质量）
REM   2. 提取 PTM/iPTM 值（全局结构质量）
REM   3. 合并所有指标到一个文件
REM   4. 生成质量分类
REM
REM 使用方法：
REM   run_full_analysis.bat <AF3_RESULTS_DIR> [OUTPUT_DIR]
REM
REM 示例：
REM   run_full_analysis.bat F:\af3_results
REM   run_full_analysis.bat F:\af3_results F:\analysis_output
REM
REM ============================================================================

setlocal enabledelayedexpansion

REM 参数检查
if "%~1"=="" (
    echo [错误] 缺少参数
    echo.
    echo 使用方法: %~nx0 ^<AF3_RESULTS_DIR^> [OUTPUT_DIR]
    echo.
    echo 示例:
    echo   %~nx0 F:\af3_results
    echo   %~nx0 F:\af3_results F:\analysis_output
    exit /b 1
)

set "RESULTS_DIR=%~1"
if "%~2"=="" (
    set "OUTPUT_DIR=.\af3_analysis_output"
) else (
    set "OUTPUT_DIR=%~2"
)

REM 检查输入目录是否存在
if not exist "%RESULTS_DIR%" (
    echo [错误] 输入目录不存在: %RESULTS_DIR%
    exit /b 1
)

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo ═══════════════════════════════════════════════════════
echo     AlphaFold3 预测结果质量分析
echo ═══════════════════════════════════════════════════════
echo.
echo 输入目录: %RESULTS_DIR%
echo 输出目录: %OUTPUT_DIR%
echo.

REM ============================================================================
REM 步骤 1: 提取 pLDDT 值
REM ============================================================================
echo [1/4] 提取 pLDDT 值（局部结构质量）...
python calc_af3_plddt_batch_improved.py ^
  --input_dir "%RESULTS_DIR%" ^
  --output_csv "%OUTPUT_DIR%\plddt_scores.csv"

if errorlevel 1 (
    echo [错误] pLDDT 提取失败
    exit /b 1
)
echo.

REM ============================================================================
REM 步骤 2: 提取 PTM/iPTM 值
REM ============================================================================
echo [2/4] 提取 PTM/iPTM 值（全局结构质量）...
python calc_af3_ptm_batch_improved.py ^
  --input_dir "%RESULTS_DIR%" ^
  --fields ptm iptm ranking_score ^
  --output_csv "%OUTPUT_DIR%\confidence_scores.csv"

if errorlevel 1 (
    echo [错误] PTM 提取失败
    exit /b 1
)
echo.

REM ============================================================================
REM 步骤 3: 合并数据
REM ============================================================================
echo [3/4] 合并所有指标...
python combine_analysis.py ^
  --plddt_csv "%OUTPUT_DIR%\plddt_scores.csv" ^
  --ptm_csv "%OUTPUT_DIR%\confidence_scores.csv" ^
  --output "%OUTPUT_DIR%\combined_scores.csv"

if errorlevel 1 (
    echo [错误] 数据合并失败
    exit /b 1
)
echo.

REM ============================================================================
REM 步骤 4: 生成汇总报告
REM ============================================================================
echo [4/4] 生成分析报告...

set "REPORT_FILE=%OUTPUT_DIR%\analysis_report.txt"

(
    echo ═══════════════════════════════════════════════════════
    echo   AlphaFold3 预测结果质量分析报告
    echo ═══════════════════════════════════════════════════════
    echo.
    echo 分析时间: %date% %time%
    echo 输入目录: %RESULTS_DIR%
    echo 输出目录: %OUTPUT_DIR%
    echo.
    echo ───────────────────────────────────────────────────────
    echo 生成的文件:
    echo ───────────────────────────────────────────────────────
    echo 1. plddt_scores.csv        - pLDDT 值（局部质量）
    echo 2. confidence_scores.csv   - PTM/iPTM 值（全局质量）
    echo 3. combined_scores.csv     - 综合评分
    echo 4. analysis_report.txt     - 本报告
    echo.
    echo ───────────────────────────────────────────────────────
    echo 质量评估标准:
    echo ───────────────────────────────────────────────────────
    echo pLDDT (局部质量):
    echo   ^> 90  : 高度可信
    echo   ^> 70  : 可信
    echo   ^> 50  : 低置信度
    echo   ^< 50  : 不可信
    echo.
    echo PTM (全局质量):
    echo   ^> 0.7 : 高度可信
    echo   ^> 0.5 : 可能可靠
    echo   ^< 0.5 : 可能不准确
    echo.
    echo 综合质量分类:
    echo   High   : pLDDT ^> 70 且 PTM ^> 0.7
    echo   Medium : pLDDT ^> 70 且 PTM ^> 0.5 或 pLDDT ^> 50 且 PTM ^> 0.7
    echo   Low    : 其他情况
    echo.
    echo ═══════════════════════════════════════════════════════
) > "!REPORT_FILE!"

type "!REPORT_FILE!"

echo.
echo ═══════════════════════════════════════════════════════
echo   ✅ 分析完成！
echo ═══════════════════════════════════════════════════════
echo.
echo 结果文件:
echo   📊 %OUTPUT_DIR%\plddt_scores.csv
echo   📊 %OUTPUT_DIR%\confidence_scores.csv
echo   📊 %OUTPUT_DIR%\combined_scores.csv
echo   📄 %OUTPUT_DIR%\analysis_report.txt
echo.
echo 提示: 查看综合结果
echo   type %OUTPUT_DIR%\combined_scores.csv
echo.

endlocal


