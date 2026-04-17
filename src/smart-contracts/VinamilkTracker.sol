// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title VinamilkTracker
 * @dev Smart Contract dùng để báo cáo và bảo vệ đồ án: Kiểm soát nguồn gốc sữa Vinamilk
 */
contract VinamilkTracker {
    
    enum Status { AtFarm, AtFactory, InTransit, AtRetailer, Sold }

    struct MilkBatch {
        string batchId;
        string farmLocation;
        Status currentStatus;
        uint256 timestamp;
        address registeredBy;
    }

    mapping(string => MilkBatch) public batches;
    string[] public batchList;

    event StatusUpdated(string batchId, Status status, string location, uint256 time);

    function registerBatch(string memory _batchId, string memory _farm) public {
        batches[_batchId] = MilkBatch({
            batchId: _batchId,
            farmLocation: _farm,
            currentStatus: Status.AtFarm,
            timestamp: block.timestamp,
            registeredBy: msg.sender
        });
        batchList.push(_batchId);
        emit StatusUpdated(_batchId, Status.AtFarm, _farm, block.timestamp);
    }

    function updateStatus(string memory _batchId, Status _newStatus, string memory _location) public {
        require(bytes(batches[_batchId].batchId).length > 0, "Batch does not exist!");
        batches[_batchId].currentStatus = _newStatus;
        batches[_batchId].timestamp = block.timestamp;
        emit StatusUpdated(_batchId, _newStatus, _location, block.timestamp);
    }

    function getBatchInfo(string memory _batchId) public view returns (string memory, Status, uint256, address) {
        MilkBatch memory b = batches[_batchId];
        return (b.farmLocation, b.currentStatus, b.timestamp, b.registeredBy);
    }
}
