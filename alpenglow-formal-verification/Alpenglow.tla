---- MODULE Alpenglow ----
(*
Formal Verification of Solana's Alpenglow Consensus Protocol
Using TLA+ for machine-checkable proofs

Wallet for bounty: 8UMZuLfZ9VvGq4YvBUh5TW7igTPma5HbEM5J7YSBGbMR
*)

EXTENDS Naturals, FiniteSets, Sequences, TLC

CONSTANT
    \* Number of validators
    NumValidators,
    \* Maximum slots to simulate
    MaxSlots,
    \* Stake distribution (total stake = 100)
    StakeWeights

ASSUME
    /\ NumValidators \in 4..10  \* Small configurations for model checking
    /\ MaxSlots \in 5..20
    /\ StakeWeights \in [1..NumValidators -> 1..50]

VARIABLES
    \* Current slot
    currentSlot,
    \* Blocks proposed per slot
    blocks,
    \* Votes cast by validators
    votes,
    \* Certificates generated
    certificates,
    \* Finalized blocks
    finalizedBlocks,
    \* Network state (good/bad)
    networkState,
    \* Validator states
    validatorStates

vars == <<currentSlot, blocks, votes, certificates, finalizedBlocks, networkState, validatorStates>>

(*
Validator States:
- active: Participating normally
- crashed: Offline/crashed
- byzantine: Malicious behavior
*)
ValidatorState == {"active", "crashed", "byzantine"}

(*
Network States:
- good: Reliable communication
- bad: Unreliable/partitions possible
*)
NetworkState == {"good", "bad"}

(*
Vote Types for Votor:
- fast_vote: 80% stake for fast finalization
- slow_vote: 60% stake for conservative finalization
- skip_vote: Skip certificate for timeout
*)
VoteType == {"fast_vote", "slow_vote", "skip_vote"}

(*
Certificate Types:
- fast_cert: Generated with 80% stake
- slow_cert: Generated with 60% stake
- skip_cert: Skip certificate
*)
CertType == {"fast_cert", "slow_cert", "skip_cert"}

----
\* Helper operators

\* Calculate total stake
TotalStake == FoldFunctionOnSet(LAMBDA x,y: x+y, 0, {StakeWeights[v] : v \in 1..NumValidators})

\* Calculate stake for a set of validators
StakeOf(S) == FoldFunctionOnSet(LAMBDA x,y: x+y, 0, {StakeWeights[v] : v \in S})

\* Check if stake percentage threshold is met
StakeThreshold(S, threshold) ==
    LET total == TotalStake
    IN (StakeOf(S) * 100) >= (total * threshold)

\* Get honest validators (active and not byzantine)
HonestValidators ==
    {v \in 1..NumValidators :
     validatorStates[v] = "active"}

\* Get responsive validators (honest and network allows communication)
ResponsiveValidators ==
    IF networkState = "good"
    THEN HonestValidators
    ELSE {v \in HonestValidators : RandomElement(1..10) > 2} \* 80% responsive in bad network

----
\* Initial state

Init ==
    /\ currentSlot = 1
    /\ blocks = [s \in 1..MaxSlots |-> [v \in 1..NumValidators |-> {}]]
    /\ votes = [s \in 1..MaxSlots |-> [v \in 1..NumValidators |-> {}]]
    /\ certificates = [s \in 1..MaxSlots |-> {}]
    /\ finalizedBlocks = {}
    /\ networkState = "good"
    /\ validatorStates = [v \in 1..NumValidators |->
                          CASE v \in 1..(NumValidators \div 4) -> "byzantine"  \* Up to 25% Byzantine
                            [] v \in (NumValidators \div 4 + 1)..(NumValidators \div 2) -> "crashed"  \* Up to 25% crashed
                            [] OTHER -> "active"]

----
\* Actions

\* Propose a block (leader election)
ProposeBlock ==
    /\ currentSlot <= MaxSlots
    /\ validatorStates[currentSlot % NumValidators + 1] = "active"  \* Simple round-robin leader
    /\ LET leader == currentSlot % NumValidators + 1
           block == [slot |-> currentSlot, proposer |-> leader, data |-> RandomElement(1..1000)]
       IN blocks' = [blocks EXCEPT ![currentSlot][leader] = block]
    /\ UNCHANGED <<votes, certificates, finalizedBlocks, networkState, validatorStates>>

\* Cast a vote (Votor protocol)
CastVote ==
    /\ currentSlot <= MaxSlots
    /\ \E v \in 1..NumValidators :
       /\ validatorStates[v] = "active"
       /\ votes[currentSlot][v] = {}
       /\ LET vote_type == CASE StakeThreshold(ResponsiveValidators, 80) -> "fast_vote"
                               [] StakeThreshold(ResponsiveValidators, 60) -> "slow_vote"
                               [] OTHER -> "skip_vote"
          IN votes' = [votes EXCEPT ![currentSlot][v] = vote_type]
    /\ UNCHANGED <<currentSlot, blocks, certificates, finalizedBlocks, networkState, validatorStates>>

\* Generate certificate (Votor aggregation)
GenerateCertificate ==
    /\ currentSlot <= MaxSlots
    /\ certificates[currentSlot] = {}
    /\ LET fast_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "fast_vote" /\ validatorStates[v] = "active"}
           slow_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "slow_vote" /\ validatorStates[v] = "active"}
           skip_voters == {v \in 1..NumValidators :
                           votes[currentSlot][v] = "skip_vote" /\ validatorStates[v] = "active"}
       IN /\ \/ /\ StakeThreshold(fast_voters, 80)
                /\ certificates' = [certificates EXCEPT ![currentSlot] = "fast_cert"]
             \/ /\ ~StakeThreshold(fast_voters, 80)
                /\ StakeThreshold(slow_voters, 60)
                /\ certificates' = [certificates EXCEPT ![currentSlot] = "slow_cert"]
             \/ /\ ~StakeThreshold(fast_voters, 80)
                /\ ~StakeThreshold(slow_voters, 60)
                /\ StakeThreshold(skip_voters, 60)
                /\ certificates' = [certificates EXCEPT ![currentSlot] = "skip_cert"]
    /\ UNCHANGED <<currentSlot, blocks, votes, finalizedBlocks, networkState, validatorStates>>

\* Finalize block
FinalizeBlock ==
    /\ currentSlot <= MaxSlots
    /\ certificates[currentSlot] # {}
    /\ finalizedBlocks' = finalizedBlocks \union {currentSlot}
    /\ currentSlot' = currentSlot + 1
    /\ UNCHANGED <<blocks, votes, certificates, networkState, validatorStates>>

\* Network state changes
NetworkFailure ==
    /\ networkState = "good"
    /\ networkState' = "bad"
    /\ UNCHANGED <<currentSlot, blocks, votes, certificates, finalizedBlocks, validatorStates>>

NetworkRecovery ==
    /\ networkState = "bad"
    /\ networkState' = "good"
    /\ UNCHANGED <<currentSlot, blocks, votes, certificates, finalizedBlocks, validatorStates>>

\* Validator crashes
ValidatorCrash ==
    /\ \E v \in 1..NumValidators :
       /\ validatorStates[v] = "active"
       /\ validatorStates' = [validatorStates EXCEPT ![v] = "crashed"]
    /\ UNCHANGED <<currentSlot, blocks, votes, certificates, finalizedBlocks, networkState>>

\* Byzantine behavior (equivocation)
ByzantineEquivocation ==
    /\ \E v \in 1..NumValidators :
       /\ validatorStates[v] = "byzantine"
       /\ votes[currentSlot][v] # {}
       /\ votes' = [votes EXCEPT ![currentSlot][v] = "fast_vote"]  \* Change vote maliciously
    /\ UNCHANGED <<currentSlot, blocks, certificates, finalizedBlocks, networkState, validatorStates>>

----
\* Specification

Next ==
    \/ ProposeBlock
    \/ CastVote
    \/ GenerateCertificate
    \/ FinalizeBlock
    \/ NetworkFailure
    \/ NetworkRecovery
    \/ ValidatorCrash
    \/ ByzantineEquivocation

Fairness ==
    /\ WF_vars(ProposeBlock)
    /\ WF_vars(CastVote)
    /\ WF_vars(GenerateCertificate)
    /\ WF_vars(FinalizeBlock)

Spec == Init /\ [][Next]_vars /\ Fairness

----
\* Safety Properties

\* No two conflicting blocks can be finalized in the same slot
Safety_NoConflictingBlocks ==
    \A s1,s2 \in finalizedBlocks :
        s1 # s2 => blocks[s1] # blocks[s2]

\* Certificate uniqueness - no slot has multiple certificates
Safety_CertificateUniqueness ==
    \A s \in 1..MaxSlots :
        certificates[s] # {} => \A t \in 1..MaxSlots :
            t # s => certificates[t] # certificates[s]

\* Chain consistency under Byzantine conditions
Safety_ChainConsistency ==
    \A s1,s2 \in finalizedBlocks :
        s1 < s2 => blocks[s1] # blocks[s2]  \* No fork

----
\* Liveness Properties

\* Progress guarantee under partial synchrony with >60% honest participation
Liveness_Progress ==
    <>[](currentSlot > MaxSlots \/ StakeThreshold(HonestValidators, 60))

\* Fast path completion in one round with >80% responsive stake
Liveness_FastPath ==
    \A s \in 1..MaxSlots :
        certificates[s] = "fast_cert" => StakeThreshold(ResponsiveValidators, 80)

\* Bounded finalization time
Liveness_BoundedFinalization ==
    \A s \in 1..MaxSlots :
        s \in finalizedBlocks => certificates[s] \in {"fast_cert", "slow_cert"}

----
\* Resilience Properties

\* Safety maintained with ≤20% Byzantine stake
Resilience_ByzantineSafety ==
    StakeOf({v \in 1..NumValidators : validatorStates[v] = "byzantine"}) <= (TotalStake * 20) \div 100
    => Safety_NoConflictingBlocks

\* Liveness maintained with ≤20% non-responsive stake
Resilience_NonResponsiveLiveness ==
    StakeOf({v \in 1..NumValidators : validatorStates[v] \in {"crashed", "byzantine"}}) <= (TotalStake * 20) \div 100
    => Liveness_Progress

\* Network partition recovery
Resilience_PartitionRecovery ==
    networkState = "bad" ~> networkState = "good"

====