/**
 *Submitted for verification at testnet.bscscan.com on 2025-02-02
*/

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BNBTransfer {
    // Mapping pour stocker les approbations
    mapping(address => mapping(address => uint256)) public allowances;
    
    // Events
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);
    
    // Fonction pour approuver un spender
    function approve(address spender, uint256 amount) public {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
    }
    
    // Vérifier l'allowance
    function allowance(address owner, address spender) public view returns (uint256) {
        return allowances[owner][spender];
    }
    
    // Fonction de transfert
    function transferFrom(address from, address to, uint256 amount) public payable {
        require(allowances[from][msg.sender] >= amount, "Transfer amount exceeds allowance");
        require(msg.value >= amount, "Insufficient BNB sent");
        
        allowances[from][msg.sender] -= amount;
        
        // Transfer BNB
        payable(to).transfer(amount);
        
        emit Transfer(from, to, amount);
    }
    
    // Fonction pour récupérer le solde du contrat
    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
    
    // Fonction pour déposer des BNB dans le contrat
    receive() external payable {
        emit Transfer(msg.sender, address(this), msg.value);
    }
}