"""Author and execute the small research notebook with captured real outputs.

No notebook runtime is required for this builder. Cells use normal Python;
JupyterLab can rerun the resulting notebook unchanged.
"""
import ast
import base64
import contextlib
import io
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def make_notebook():
    cells=[]
    def md(text): cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(True)})
    def code(text): cells.append({'cell_type':'code','metadata':{},'source':text.splitlines(True),'execution_count':None,'outputs':[]})
    md('# UAC Insight: Care Load Dynamics and Seven-Day Forecasting\n\n**Data Science internship project — Harish V J**\n\nResearch question: How do reported care loads and flows evolve, and does a seven-day HHS-care model outperform persistence? This notebook preserves the source, validates the observations, builds interpretable indicators, and evaluates models chronologically.')
    code("""# Locate the project whether this notebook is opened from the root or notebooks/.
from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / 'src').exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import matplotlib.pyplot as plt
from src.data import read_source
from src.features import derive
from src.analysis import summarize
from src.models import run_experiment, prepare
from scripts.build_project import style, plot_load, plot_flows, plot_models, plot_predictions, plot_sensitivity
style()
""")
    md('## 1. Preserve and audit the source\nOnly fully blank records are removed. Invalid counts and duplicate dates cause validation to fail instead of being silently repaired. A SHA-256 checksum identifies the exact supplied file.')
    code("raw, audit = read_source()\npd.DataFrame([audit]).T.rename(columns={0: 'value'})")
    md('## 2. Create a canonical analytical table\nStocks and flows retain different meanings. Rolling windows count reported observations. Missing dates are not zero-filled. The first 14-observation indicators remain missing until the complete window exists.')
    code("data = derive(raw)\ndata[['date','hhs_care','total_load','net_flow','gap_days','load_mean7','volatility14']].head(16)")
    code("bundle = summarize(raw)\npd.DataFrame([bundle['summary']]).T.rename(columns={0: 'value'})")
    md('## 3. Explore long-term load and flow patterns\nThe chart uses actual calendar dates. Lines connect reported endpoints without creating unobserved rows.')
    code('plot_load(data)')
    code("pd.DataFrame(bundle['yearly']).rename(columns={'date':'year'})")
    code('plot_flows(data)')
    md('## 4. Test the persistence-rule assumption\nA pressure indicator requires a positive rolling net-flow sum and a minimum count of positive observations. Three conventions are compared; none is an official operational threshold.')
    code("pd.DataFrame(bundle['sensitivity'])")
    code('plot_sensitivity(bundle)')
    md('## 5. Examine associations cautiously\nRank association describes co-movement. Common trends and time dependence prevent causal interpretation.')
    code("data[['cbp_intake','cbp_custody','transfers','hhs_care','discharges','net_flow']].corr(method='spearman').round(3)")
    md('## 6. Construct exact seven-day targets and evaluate models\nAn origin is eligible only when HHS care was reported exactly seven calendar days later. Features contain current and earlier values. The 70/15/15 chronological boundaries are applied before fitting; pairs whose targets cross a boundary are excluded. Ridge scaling is fit inside the training pipeline. Validation MAE selects the model, and test data never determine the winner. The candidate configurations are fixed, not optimized against the test set.')
    code("experiment = run_experiment(raw)\npd.json_normalize(experiment['scores'])")
    code("pd.DataFrame([experiment['split']]).T.rename(columns={0:'value'})")
    code("# Explicit evidence that labels cannot cross into the next partition.\nassert experiment['split']['train_last_target'] < experiment['split']['validation_start']\nassert experiment['split']['validation_last_target'] < experiment['split']['test_start']\nprint('Both temporal leakage checks passed.')\nprint('Chosen on validation:', experiment['selected_model'])\nprint('Test MAE improvement over persistence:', experiment['test_skill_vs_persistence_pct'], '%')")
    code('plot_models(experiment)')
    code('plot_predictions(experiment)')
    md('## 7. Interpret a forward estimate from the historical cutoff\nThis estimate starts at the last supplied observation. It is not a present-day live forecast. The absolute-validation-error reference band is not a calibrated confidence interval.')
    code("pd.DataFrame([experiment['forecast']]).T.rename(columns={0:'value'})")
    md('## 8. Conclusions and next steps\nThe report compares validation and test performance instead of asserting a percentage accuracy. Baseline comparison determines whether model complexity provides value. The dataset supports retrospective load monitoring and flow-pressure indicators, but it does not provide capacity, staffing, or individual-level outcomes.\n\nFuture work: acquire defined reporting timestamps and capacity denominators; test additional historical rolling origins; assess stability across regimes; evaluate missing-target selection bias; and monitor drift before operational use.\n\n**Reproduction:** `python scripts/build_project.py` regenerates the numerical tables and figures from the raw CSV. `python -m unittest discover -s tests -v` checks validation, formulas, temporal boundaries, and API workflows.')
    namespace={'__name__':'__notebook__'}
    os.chdir(ROOT)
    from matplotlib.figure import Figure
    from matplotlib import pyplot as plt
    count=0
    for cell in cells:
        if cell['cell_type']!='code': continue
        count+=1;cell['execution_count']=count
        source=''.join(cell['source']);parsed=ast.parse(source);last=None
        if parsed.body and isinstance(parsed.body[-1],ast.Expr):last=parsed.body.pop()
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            exec(compile(parsed,'notebook','exec'),namespace)
            value=eval(compile(ast.Expression(last.value),'notebook','eval'),namespace) if last else None
        if stream.getvalue():cell['outputs'].append({'output_type':'stream','name':'stdout','text':stream.getvalue().splitlines(True)})
        if value is not None:
            if isinstance(value,Figure):
                buffer=io.BytesIO();value.savefig(buffer,format='png',bbox_inches='tight',dpi=120)
                data={'image/png':base64.b64encode(buffer.getvalue()).decode(),'text/plain':['<Figure generated by this cell>']};plt.close(value)
            else:
                data={'text/plain':repr(value).splitlines(True)}
                if hasattr(value,'to_html'):data['text/html']=value.to_html().splitlines(True)
            cell['outputs'].append({'output_type':'execute_result','execution_count':count,'data':data,'metadata':{}})
    notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':4}
    path=ROOT/'notebooks/01_research_workflow.ipynb';path.write_text(json.dumps(notebook,indent=1))
    print(f'Executed {count} cells with no errors: {path.name}')


if __name__=='__main__':make_notebook()
