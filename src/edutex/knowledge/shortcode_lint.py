"""Static linting for EduTeX shortcode authoring."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from .parser import ParseError, parse

INTERACTIVE_TYPES={"cloze","short_answer","short-answer","true_false","true-false","builder","sentence-builder","matching","translation","choice"}

@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    suggestion: str|None=None
    path: str|None=None
    line: int|None=None
    column: int|None=1
    shortcode: str|None=None
    def to_dict(self)->dict[str,Any]:
        result={"severity":self.severity,"code":self.code,"message":self.message}
        for key in ("suggestion","path","line","column","shortcode"):
            value=getattr(self,key)
            if value is not None: result[key]=value
        return result

@dataclass
class LintReport:
    path: str="<string>"
    errors: list[Diagnostic]=field(default_factory=list)
    warnings: list[Diagnostic]=field(default_factory=list)
    @property
    def valid(self): return not self.errors
    @property
    def diagnostics(self): return [*self.errors,*self.warnings]
    def to_dict(self): return {"path":self.path,"valid":self.valid,"errors":[item.to_dict() for item in self.errors],"warnings":[item.to_dict() for item in self.warnings]}
    def to_json(self): return json.dumps(self.to_dict(),ensure_ascii=False,indent=2)

class ShortcodeLinter:
    def lint(self,source:str,*,path:str="<string>")->LintReport:
        report=LintReport(path=path)
        try: ast=parse(source)
        except ParseError as exc:
            self._add_parse_error(report,exc); return report
        except (ValueError,TypeError) as exc:
            self._add(report,"error","SC006",str(exc),"Check the shortcode opening line and delimiter syntax."); return report
        for node in ast:
            if node.get("kind")=="shortcode": self._lint_node(node,report)
        return report
    def lint_file(self,path:str|Path)->LintReport:
        source_path=Path(path); return self.lint(source_path.read_text(encoding="utf-8"),path=str(source_path))
    def _lint_node(self,node,report):
        node_type=str(node.get("type","")); subtype=node.get("subtype"); fields=[str(v).strip() for v in node.get("fields",[])]; body=str(node.get("body","")); line=node.get("line"); shortcode=node_type+(f".{subtype}" if subtype else "")
        self._lint_fields(node_type,fields,report,line,shortcode)
        self._lint_special(node_type,subtype,fields,body,node,report,line,shortcode)
        for child in node.get("children",[]):
            if isinstance(child,dict) and child.get("kind")=="shortcode": self._lint_node(child,report)
    def _lint_fields(self,node_type,fields,report,line,shortcode):
        if not fields:return
        limits={"vocab":(2,5),"verb":(1,5),"conjugation":(1,2)}
        if node_type not in limits:return
        minimum,maximum=limits[node_type]
        if not minimum<=len(fields)<=maximum:
            self._add(report,"error","SC102",f"{node_type} expects {minimum}-{maximum} pipe-separated fields; got {len(fields)}.",f"Use the documented field order for {node_type}.",line=line,shortcode=shortcode)
        elif not fields[0]: self._add(report,"error","SC101",f"{node_type} requires a non-empty first field.",f"Provide the first {node_type} field.",line=line,shortcode=shortcode)
    def _lint_special(self,node_type,subtype,fields,body,node,report,line,shortcode):
        if node_type in {"rule", "note", "example", "solution"} and not body.strip():
            self._add(report,"error","SC106",f"{node_type} requires a non-empty body.",f"Add content between the {node_type} shortcode delimiters.",line=line,shortcode=shortcode)
        if node_type=="formula":
            if subtype not in {"math","chem"}: self._add(report,"error","SC103","formula requires the math or chem subtype.","Use ::: formula.math or ::: formula.chem.",line=line,shortcode=shortcode)
            if not body.strip(): self._add(report,"error","SC101","formula requires a non-empty body.","Add the formula between the shortcode delimiters.",line=line,shortcode=shortcode)
        if node_type=="example" and subtype=="comparative" and not any(item.strip().startswith(("+","-")) for item in body.splitlines() if item.strip()): self._add(report,"warning","SC204","Comparative example has no + or - entry.","Prefix correct lines with + and incorrect lines with -.",line=line,shortcode=shortcode)
        if node_type=="exercise":
            children=[item for item in node.get("children",[]) if item.get("type")=="solution"]
            if not children:self._add(report,"warning","SC201","Exercise has no nested solution.","Add a solution shortcode before the exercise closing delimiter.",line=line,shortcode=shortcode)
            self._lint_exercise(body,children,report,line,shortcode)
    def _lint_exercise(self,body,solutions,report,line,shortcode):
        declared=""
        for raw in body.splitlines():
            match=re.match(r"^\s*type\s*:\s*(\S+)\s*$",raw,re.IGNORECASE)
            if match: declared=match.group(1).lower(); break
        if not declared:return
        if declared not in INTERACTIVE_TYPES:
            self._add(report,"error","SC104",f"Unknown interactive exercise type '{declared}'.","Use a supported interactive exercise type.",line=line,shortcode=shortcode); return
        lines=[item.strip() for item in body.splitlines() if item.strip()]; lower=[item.lower() for item in lines]; solution_body="\n".join(item.get("body","") for item in solutions).strip()
        if declared=="cloze": self._require(any(item.startswith("sentence:") for item in lower) and any(item.startswith("answers:") or item.startswith("-") for item in lower),"cloze requires a sentence and at least one answer.",report,line,shortcode)
        elif declared in {"short_answer","short-answer"}: self._require(any(item.startswith(("prompt:","question:")) for item in lower) and (any(item.startswith(("answer:","expected:")) for item in lower) or bool(solution_body)),"short answer requires a prompt and an expected answer.",report,line,shortcode)
        elif declared in {"true_false","true-false"}:
            statements=sum(item.startswith("statement:") for item in lower); answers=sum(item.startswith("answer:") for item in lower); self._require(statements>0 and statements==answers,"true/false requires matching statement and answer entries.",report,line,shortcode)
        elif declared in {"builder","sentence-builder"}: self._require(len([item for item in lines if item.startswith("-")])>=2,"sentence builder requires at least two tokens.",report,line,shortcode)
        elif declared=="matching":
            words=self._list_after(lines,"words:"); meanings=self._list_after(lines,"meanings:"); self._require(bool(words) and len(words)==len(meanings),"matching requires equally sized words and meanings lists.",report,line,shortcode)
        elif declared=="translation": self._require(any(item.startswith(("source:","text:","prompt:")) for item in lower),"translation requires source text.",report,line,shortcode)
        elif declared=="choice":
            options=self._list_after(lines,"options:"); self._require(any(item.startswith(("question:","prompt:")) for item in lower) and len(options)>=2,"choice requires a question and at least two options.",report,line,shortcode)
    @staticmethod
    def _list_after(lines,marker):
        try:start=next(index for index,line in enumerate(lines) if line.lower()==marker)
        except StopIteration:return []
        result=[]
        for line in lines[start+1:]:
            if not line.startswith("-"):break
            result.append(line[1:].strip())
        return result
    def _require(self,valid,message,report,line,shortcode):
        if not valid:self._add(report,"error","SC105",message,"Add the required exercise data.",line=line,shortcode=shortcode)
    def _add_parse_error(self,report,error):
        message=str(error); line=getattr(error,"line",None)
        prefix=f"Line {line}: "
        if message.startswith(prefix):message=message[len(prefix):]
        code="SC003" if "Unclosed shortcode" in message else "SC004" if "may only appear nested" in message else "SC005" if "does not support nested" in message or "Only a solution" in message else "SC002" if "Unknown subtype" in message else "SC001" if "Unknown shortcode type" in message else "SC006"
        self._add(report,"error",code,message,"Fix the shortcode syntax and run lint again.",line=line)
    @staticmethod
    def _add(report,severity,code,message,suggestion=None,*,line=None,shortcode=None):
        item=Diagnostic(severity,code,message,suggestion,report.path,line,1,shortcode); (report.errors if severity=="error" else report.warnings).append(item)

def lint_source(source,*,path="<string>"):return ShortcodeLinter().lint(source,path=path)
def lint_file(path):return ShortcodeLinter().lint_file(path)
def format_text(report):
    lines=[]
    for item in report.diagnostics:
        location=f"{item.path}:{item.line}:{item.column}" if item.line else str(item.path); lines.append(f"{item.severity.upper()} {location} [{item.code}] {item.message}")
        if item.suggestion:lines.append(f"Suggestion: {item.suggestion}")
    if not lines:lines=[f"OK  {report.path}","No shortcode errors found."]
    lines.append(f"{len(report.errors)} errors, {len(report.warnings)} warnings."); return "\n".join(lines)
