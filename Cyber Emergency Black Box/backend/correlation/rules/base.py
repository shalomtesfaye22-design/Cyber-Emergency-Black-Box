from dataclasses import dataclass
@dataclass
class RuleResult:
    rule_id:str; name:str; severity:str; event_ids:list[str]; explanation:str; recommendations:list[str]
class BaseRule:
    rule_id=""; name=""; severity="MEDIUM"; time_window_seconds=600
    def evaluate(self,events): raise NotImplementedError
