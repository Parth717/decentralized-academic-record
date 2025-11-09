package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// ---------- Data Model ----------

type Credential struct {
	CredID        string `json:"credID"`
	StudentID     string `json:"studentID"`
	StudentName   string `json:"studentName"`
	University    string `json:"university"`
	Degree        string `json:"degree"`
	GPA           string `json:"gpa"`
	IssueDate     string `json:"issueDate"`
	Hash          string `json:"hash"`
	Status        string `json:"status"` // issued / revoked
	OwnerMSP      string `json:"ownerMSP"`
	SharedWithMSP string `json:"sharedWithMSP"` // always present, may be ""
}

// ---------- Smart Contract ----------

type SmartContract struct {
	contractapi.Contract
}

// ---------- Issue ----------

func (s *SmartContract) IssueCredential(ctx contractapi.TransactionContextInterface,
	credID, studentID, studentName, university, degree, gpa, issueDate, hash string) error {

	exists, err := s.CredentialExists(ctx, credID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("credential %s already exists", credID)
	}

	mspid, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return fmt.Errorf("cannot get MSP ID: %v", err)
	}

	cred := Credential{
		CredID:        credID,
		StudentID:     studentID,
		StudentName:   studentName,
		University:    university,
		Degree:        degree,
		GPA:           gpa,
		IssueDate:     issueDate,
		Hash:          hash,
		Status:        "issued",
		OwnerMSP:      mspid,
		SharedWithMSP: "", // always present
	}

	data, _ := json.Marshal(cred)
	return ctx.GetStub().PutPrivateData("Org1PrivateCollection", credID, data)
}

// ---------- Read (Org1 only) ----------

func (s *SmartContract) ReadCredential(ctx contractapi.TransactionContextInterface, credID string) (*Credential, error) {
	data, err := ctx.GetStub().GetPrivateData("Org1PrivateCollection", credID)
	if err != nil {
		return nil, err
	}
	if data == nil {
		return nil, fmt.Errorf("credential %s not found", credID)
	}

	var cred Credential
	if err := json.Unmarshal(data, &cred); err != nil {
		return nil, err
	}
	if cred.SharedWithMSP == "" {
		cred.SharedWithMSP = ""
	}
	return &cred, nil
}

// ---------- Write for Org2 (called by Org2) ----------

func (s *SmartContract) StoreCredentialForOrg2(ctx contractapi.TransactionContextInterface, credJSON string) error {
	mspid, _ := ctx.GetClientIdentity().GetMSPID()
	if mspid != "Org2MSP" {
		return fmt.Errorf("only Org2 can write into Org2PrivateCollection")
	}

	var cred Credential
	if err := json.Unmarshal([]byte(credJSON), &cred); err != nil {
		return fmt.Errorf("invalid credential json: %v", err)
	}
	if cred.CredID == "" {
		return fmt.Errorf("credID required in credential json")
	}

	cred.SharedWithMSP = "Org2MSP"
	data, _ := json.Marshal(cred)
	return ctx.GetStub().PutPrivateData("Org2PrivateCollection", cred.CredID, data)
}

// ---------- Verify (Org2 read) ----------

func (s *SmartContract) VerifyCredential(ctx contractapi.TransactionContextInterface, credID string) (*Credential, error) {
	mspid, _ := ctx.GetClientIdentity().GetMSPID()
	if mspid != "Org2MSP" {
		return nil, fmt.Errorf("only Org2 can verify credentials")
	}

	data, err := ctx.GetStub().GetPrivateData("Org2PrivateCollection", credID)
	if err != nil {
		return nil, err
	}
	if data == nil {
		return nil, fmt.Errorf("credential %s not found in Org2 collection", credID)
	}

	var cred Credential
	if err := json.Unmarshal(data, &cred); err != nil {
		return nil, err
	}
	if cred.SharedWithMSP == "" {
		cred.SharedWithMSP = "Org2MSP"
	}
	return &cred, nil
}

// ---------- Revoke (Org1 only) ----------

func (s *SmartContract) RevokeCredential(ctx contractapi.TransactionContextInterface, credID string) error {
	mspid, _ := ctx.GetClientIdentity().GetMSPID()
	if mspid != "Org1MSP" {
		return fmt.Errorf("only Org1 can revoke credentials")
	}

	data, err := ctx.GetStub().GetPrivateData("Org1PrivateCollection", credID)
	if err != nil {
		return err
	}
	if data == nil {
		return fmt.Errorf("credential %s not found", credID)
	}

	var cred Credential
	if err := json.Unmarshal(data, &cred); err != nil {
		return err
	}
	cred.Status = "revoked"
	if cred.SharedWithMSP == "" {
		cred.SharedWithMSP = ""
	}

	newData, _ := json.Marshal(cred)
	return ctx.GetStub().PutPrivateData("Org1PrivateCollection", credID, newData)
}

// ---------- Exists Helper ----------

func (s *SmartContract) CredentialExists(ctx contractapi.TransactionContextInterface, credID string) (bool, error) {
	data, err := ctx.GetStub().GetPrivateData("Org1PrivateCollection", credID)
	if err != nil {
		return false, err
	}
	return data != nil, nil
}

// ---------- Main ----------

func main() {
	cc, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		panic(fmt.Sprintf("error creating chaincode: %v", err))
	}
	if err := cc.Start(); err != nil {
		panic(fmt.Sprintf("error starting chaincode: %v", err))
	}
}
