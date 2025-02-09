// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CollaborativePayment {
    struct PaymentGroup {
        address owner;
        uint256 targetAmount;
        bool completed;
        mapping(address => uint256) contributions;
        address[] contributors;
        address payable beneficiary;
    }

    mapping(bytes32 => PaymentGroup) public paymentGroups;
    mapping(address => mapping(address => uint256)) public allowances;

    event GroupCreated(bytes32 indexed groupId, address owner, uint256 targetAmount);
    event Contribution(bytes32 indexed groupId, address contributor, uint256 amount);
    event GroupCompleted(bytes32 indexed groupId, uint256 totalAmount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    function createPaymentGroup(
        uint256 _targetAmount,
        address payable _beneficiary
    ) public returns (bytes32) {
        require(_targetAmount > 0, "Target amount must be greater than 0");
        require(_beneficiary != address(0), "Invalid beneficiary address");

        bytes32 groupId = keccak256(abi.encodePacked(
            msg.sender,
            _targetAmount,
            block.timestamp
        ));

        PaymentGroup storage newGroup = paymentGroups[groupId];
        newGroup.owner = msg.sender;
        newGroup.targetAmount = _targetAmount;
        newGroup.completed = false;
        newGroup.beneficiary = _beneficiary;

        emit GroupCreated(groupId, msg.sender, _targetAmount);
        return groupId;
    }

    function approve(address spender, uint256 amount) public {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
    }

    function allowance(address owner, address spender) public view returns (uint256) {
        return allowances[owner][spender];
    }

    function contribute(bytes32 groupId, address from) public payable {
        PaymentGroup storage group = paymentGroups[groupId];
        require(!group.completed, "Group payment already completed");
        require(msg.value > 0, "Must send some BNB");

        if(from != msg.sender) {
            require(allowances[from][msg.sender] >= msg.value, "Transfer amount exceeds allowance");
            allowances[from][msg.sender] -= msg.value;
        }

        if(group.contributions[from] == 0) {
            group.contributors.push(from);
        }
        group.contributions[from] += msg.value;

        emit Contribution(groupId, from, msg.value);

        uint256 totalContributed = getGroupBalance(groupId);
        if(totalContributed >= group.targetAmount) {
            completePayment(groupId);
        }
    }

    function completePayment(bytes32 groupId) private {
        PaymentGroup storage group = paymentGroups[groupId];
        require(!group.completed, "Payment already completed");

        group.completed = true;
        uint256 totalAmount = getGroupBalance(groupId);
        group.beneficiary.transfer(totalAmount);

        emit GroupCompleted(groupId, totalAmount);
    }

    function getGroupBalance(bytes32 groupId) public view returns (uint256) {
        PaymentGroup storage group = paymentGroups[groupId];
        uint256 total = 0;
        for(uint i = 0; i < group.contributors.length; i++) {
            total += group.contributions[group.contributors[i]];
        }
        return total;
    }

    function getContribution(bytes32 groupId, address contributor) public view returns (uint256) {
        return paymentGroups[groupId].contributions[contributor];
    }

    function getGroupDetails(bytes32 groupId) public view returns (
        address owner,
        uint256 targetAmount,
        bool completed,
        address[] memory contributors,
        address beneficiary
    ) {
        PaymentGroup storage group = paymentGroups[groupId];
        return (
            group.owner,
            group.targetAmount,
            group.completed,
            group.contributors,
            group.beneficiary
        );
    }

    receive() external payable {}
}
