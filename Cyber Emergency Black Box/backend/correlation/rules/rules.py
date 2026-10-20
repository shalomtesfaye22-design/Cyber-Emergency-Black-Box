from backend.correlation.rules.base import BaseRule, RuleResult
class AccountCompromiseRule(BaseRule):
    rule_id="R-01"; name="Possible Account Compromise"; severity="HIGH"
    def evaluate(self,e):
        for success_i,x in enumerate(e):
            if x.event_type != "login_success": continue
            failures=[a for a in e[:success_i] if a.event_type=="login_failure" and a.user_name==x.user_name and (x.timestamp-a.timestamp).total_seconds()<=600]
            follow=next((a for a in e[success_i+1:] if a.event_type in {"process_start","file_modified","network_connection"} and (a.timestamp-x.timestamp).total_seconds()<=600),None)
            if len(failures)>=3 and follow: return RuleResult(self.rule_id,self.name,self.severity,[a.event_id for a in failures]+[x.event_id,follow.event_id],f"Multiple failed logins for {x.user_name}, then a successful login and follow-up activity.",["Verify account ownership and review the linked activity."])
class SuspiciousProcessRule(BaseRule):
    rule_id="R-02"; name="Suspicious Process Sequence"; severity="HIGH"
    def evaluate(self,e):
        for p in e:
            if p.event_type!="process_start": continue
            files=[x for x in e if x.process_name==p.process_name and x.event_type in {"file_created","file_modified"} and 0 <= (x.timestamp-p.timestamp).total_seconds()<=600]
            net=next((x for x in e if x.process_name==p.process_name and x.event_type=="network_connection" and 0 <= (x.timestamp-p.timestamp).total_seconds()<=600),None)
            if len(files)>=2 and net: return RuleResult(self.rule_id,self.name,self.severity,[p.event_id]+[x.event_id for x in files]+[net.event_id],f"Process {p.process_name} modified files then opened a network connection.",["Review process provenance and destination."])
class FileActivityRule(BaseRule):
    rule_id="R-03"; name="Unusual File Modification Activity"; severity="MEDIUM"; time_window_seconds=300
    def evaluate(self,e):
        files=[x for x in e if x.event_type in {"file_created","file_modified","file_deleted"}]
        for x in files:
            match=[a for a in files if 0 <= (a.timestamp-x.timestamp).total_seconds()<=300]
            if len(match)>=5: return RuleResult(self.rule_id,self.name,self.severity,[a.event_id for a in match],"High-volume file activity was observed in a short interval.",["Review affected files and responsible process."])
