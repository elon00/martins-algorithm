---- MODULE Votor ----
(*
Formal Specification of Votor: Alpenglow's Dual-Path Voting Protocol
*)

EXTENDS Naturals, FiniteSets, Sequences, TLC

CONSTANT
    NumValidators,
    StakeWeights

VARIABLES
    currentSlot,
    votes,
    certificates,
    validatorStates

vars == <<currentSlot, votes, certificates, validatorStates>>

VoteType == {"fast_vote", "slow_vote", "skip_vote"}
CertType == {"fast_cert", "slow_cert", "skip_cert"}

\* Calculate total stake
TotalStake == FoldFunctionOnSet(LAMBDA x,y: x+y, 0, {StakeWeights[v] : v \in 1..NumValidators})

\* Calculate stake for a set of validators
StakeOf(S) == FoldFunctionOnSet(LAMBDA x,y: x+y, 0, {StakeWeights[v] : v \in S})

\* Check if stake percentage threshold is met
StakeThreshold(S, threshold) ==
    LET total == TotalStake
    IN (StakeOf(S) * 100) >= (total * threshold)

\* Get honest validators
HonestValidators ==
    {v \in 1..NumValidators : validatorStates[v] = "active"}

\* Get responsive validators (simplified for formal verification)
ResponsiveValidators == HonestValidators

----
\* Votor Actions

\* Cast fast vote (80% threshold for immediate finalization)
CastFastVote ==
    /\ \E v \in ResponsiveValidators :
       /\ votes[currentSlot][v] = {}
       /\ StakeThreshold(ResponsiveValidators, 80)  \* Network condition for fast path
       /\ votes' = [votes EXCEPT ![currentSlot][v] = "fast_vote"]
    /\ UNCHANGED <<currentSlot, certificates, validatorStates>>

\* Cast slow vote (60% threshold for conservative finalization)
CastSlowVote ==
    /\ \E v \in ResponsiveValidators :
       /\ votes[currentSlot][v] = {}
       /\ ~StakeThreshold(ResponsiveValidators, 80)  \* Fast path not available
       /\ StakeThreshold(ResponsiveValidators, 60)   \* Slow path available
       /\ votes' = [votes EXCEPT ![currentSlot][v] = "slow_vote"]
    /\ UNCHANGED <<currentSlot, certificates, validatorStates>>

\* Cast skip vote (timeout mechanism)
CastSkipVote ==
    /\ \E v \in ResponsiveValidators :
       /\ votes[currentSlot][v] = {}
       /\ ~StakeThreshold(ResponsiveValidators, 60)  \* Neither fast nor slow path available
       /\ votes' = [votes EXCEPT ![currentSlot][v] = "skip_vote"]
    /\ UNCHANGED <<currentSlot, certificates, validatorStates>>

\* Aggregate votes into certificate (Votor's core logic)
AggregateVotes ==
    /\ certificates[currentSlot] = {}
    /\ LET fast_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "fast_vote" /\ validatorStates[v] = "active"}
           slow_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "slow_vote" /\ validatorStates[v] = "active"}
           skip_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "skip_vote" /\ validatorStates[v] = "active"}
       IN \/ /\ StakeThreshold(fast_voters, 80)
             /\ certificates' = [certificates EXCEPT ![currentSlot] = "fast_cert"]
          \/ /\ ~StakeThreshold(fast_voters, 80)
             /\ StakeThreshold(slow_voters, 60)
             /\ certificates' = [certificates EXCEPT ![currentSlot] = "slow_cert"]
          \/ /\ ~StakeThreshold(fast_voters, 80)
             /\ ~StakeThreshold(slow_voters, 60)
             /\ StakeThreshold(skip_voters, 60)
             /\ certificates' = [certificates EXCEPT ![currentSlot] = "skip_cert"]
    /\ UNCHANGED <<currentSlot, votes, validatorStates>>

----
\* Votor Properties

\* Fast path property: 80% stake enables fast finalization
Votor_FastPathProperty ==
    \A s \in 1..10 :
        certificates[s] = "fast_cert" =>
            LET fast_voters == {v \in 1..NumValidators : votes[s][v] = "fast_vote"}
            IN StakeThreshold(fast_voters, 80)

\* Slow path property: 60% stake enables conservative finalization
Votor_SlowPathProperty ==
    \A s \in 1..10 :
        certificates[s] = "slow_cert" =>
            LET slow_voters == {v \in 1..NumValidators : votes[s][v] = "slow_vote"}
            IN StakeThreshold(slow_voters, 60) /\ ~StakeThreshold(slow_voters, 80)

\* Skip certificate property: Used when neither fast nor slow paths available
Votor_SkipProperty ==
    \A s \in 1..10 :
        certificates[s] = "skip_cert" =>
            LET fast_voters == {v \in 1..NumValidators : votes[s][v] = "fast_vote"}
                slow_voters == {v \in 1..NumValidators : votes[s][v] = "slow_vote"}
            IN ~StakeThreshold(fast_voters, 80) /\ ~StakeThreshold(slow_voters, 60)

\* Certificate uniqueness: Only one certificate per slot
Votor_CertificateUniqueness ==
    \A s1,s2 \in 1..10 :
        s1 # s2 /\ certificates[s1] # {} /\ certificates[s2] # {} =>
            certificates[s1] # certificates[s2]

\* Progress property: Some certificate is eventually generated
Votor_Progress ==
    \A s \in 1..10 :
        <>(certificates[s] # {})

\* Byzantine resilience: Safety maintained with ≤20% Byzantine stake
Votor_ByzantineResilience ==
    LET byzantine_stake == StakeOf({v \in 1..NumValidators : validatorStates[v] = "byzantine"})
    IN byzantine_stake <= (TotalStake * 20) \div 100 => Votor_CertificateUniqueness

====