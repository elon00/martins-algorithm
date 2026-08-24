class PolicyEngine:
    def evaluate(self, opt):
        if opt.get('status') not in ['RECOVERABLE', 'MIGRATED', 'ACTIVE'] or opt.get('martin_score', 0) < 50.0:
            return {'action': 'DENIED', 'reason': 'Failed Security Threshold'}
        return {'action': 'REQUIRE_HUMAN_APPROVAL', 'reason': 'Passed AI Checks. Awaiting User Wallet Signature.'}
