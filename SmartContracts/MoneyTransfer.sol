// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MobileMoneyToken is ERC20, Ownable {
    mapping(address => bool) public authorizedOperators;
    
    constructor() ERC20("Mobile Money Token", "MMT") {
        _mint(msg.sender, 1000000 * 10**decimals()); // Initial supply
    }
    
    // Permet d'ajouter ou retirer des opérateurs autorisés (le backend)
    function setOperator(address operator, bool status) public onlyOwner {
        authorizedOperators[operator] = status;
    }
    
    // Override du transferFrom pour ajouter la vérification des opérateurs
    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) public virtual override returns (bool) {
        require(
            authorizedOperators[msg.sender] || allowance(sender, msg.sender) >= amount,
            "Transfer amount exceeds allowance and sender is not an authorized operator"
        );
        
        _transfer(sender, recipient, amount);
        
        // Si ce n'est pas un opérateur autorisé, on réduit l'allowance
        if (!authorizedOperators[msg.sender]) {
            _approve(sender, msg.sender, allowance(sender, msg.sender) - amount);
        }
        
        return true;
    }
    
    // Fonction pour déposer des BNB et recevoir des tokens
    function deposit() public payable {
        require(msg.value > 0, "Must send BNB");
        _mint(msg.sender, msg.value);
    }
    
    // Fonction pour retirer des BNB en brûlant des tokens
    function withdraw(uint256 amount) public {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
        payable(msg.sender).transfer(amount);
    }
}