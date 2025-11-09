package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
	"github.com/hyperledger/fabric-chaincode-go/v2/pkg/cid"
)

const collection = "credPDC"

// Public index (world state)
type CredentialPublic struct {
	CredentialID string   `json:"credentialID"`
	StudentID    string   `json:"studentID"`   // opaque (e.g., roll no. or hash)
	University   string   `json:"university"`
	Status       string   `json:"status"`      // Issued | Shared | Revoked
	Hash         string   `json:"hash"`        // hash of private payload
	IssueDate    string   `json:"issueDate"`
	SharedWith   []string `json:"sharedWith"`  // MSP IDs allowed (logical)
}

// Private payload (lives in PDC)
type CredentialPrivate struct {
	CredentialID string `json:"credentialID"`
	StudentName  string `json:"studentName"`
	University   string `json:"university"`
	Degree       string `json:"degree"`
	GPA          string `json:"gpa"`
	IssueDate    string `json:"issueDate"`
}

type Contract struct{ contractapi.Contract }

func (c *Contract) IssueCredential(ctx contractapi.TransactionContextInterface,
	credID, studentID, studentName, university, degree, gpa, issueDate, hash string) error {

	msp, err := cid.GetMSPID(ctx.GetStub())
	if err != nil {
		return err
	}
	if msp != "Org1MSP" { // University only
		return fmt.Errorf("only University (Org1MSP) can issue")
	}

	exists, err := ctx.GetStub().GetState("cred:" + credID)
	if err != nil {
		return err
	}
	if exists != nil {
		return fmt.Errorf("credential already exists")
	}

	pub := &CredentialPublic{
		CredentialID: credID, StudentID: studentID, University: university,
		Status: "Issued", Hash: hash, IssueDate: issueDate, SharedWith: []string{},
	}
	pubB, _ := json.Marshal(pub)
	if err := ctx.GetStub().PutState("cred:"+credID, pubB); err != nil {
		return err
	}

	priv := &CredentialPrivate{
		CredentialID: credID, StudentName: studentName, University: university,
		Degree: degree, GPA: gpa, IssueDate: issueDate,
	}
	privB, _ := json.Marshal(priv)
	return ctx.GetStub().PutPrivateData(collection, "credpriv:"+credID, privB)
}

func (c *Contract) ShareCredential(ctx contractapi.TransactionContextInterface, credID, targetMSP string) error {
	role, found, _ := cid.GetAttributeValue(ctx.GetStub(), "role")
	if !found || role != "student" {
		return fmt.Errorf("only Student (role=student) can share")
	}

	pubB, err := ctx.GetStub().GetState("cred:" + credID)
	if err != nil || pubB == nil {
		return fmt.Errorf("credential not found")
	}
	var pub CredentialPublic
	_ = json.Unmarshal(pubB, &pub)
	if pub.Status == "Revoked" {
		return fmt.Errorf("credential revoked")
	}
	already := false
	for _, m := range pub.SharedWith {
		if m == targetMSP {
			already = true
			break
		}
	}
	if !already {
		pub.SharedWith = append(pub.SharedWith, targetMSP)
		pub.Status = "Shared"
	}
	newB, _ := json.Marshal(pub)
	return ctx.GetStub().PutState("cred:"+credID, newB)
}

func (c *Contract) RevokeCredential(ctx contractapi.TransactionContextInterface, credID string) error {
	msp, _ := cid.GetMSPID(ctx.GetStub())
	if msp != "Org1MSP" {
		return fmt.Errorf("only University may revoke")
	}
	pubB, _ := ctx.GetStub().GetState("cred:" + credID)
	if pubB == nil {
		return fmt.Errorf("not found")
	}
	var pub CredentialPublic
	_ = json.Unmarshal(pubB, &pub)
	pub.Status = "Revoked"
	newB, _ := json.Marshal(pub)
	return ctx.GetStub().PutState("cred:"+credID, newB)
}

// For verifiers (Org2)
func (c *Contract) VerifyCredential(ctx contractapi.TransactionContextInterface, credID string) (*CredentialPrivate, error) {
	msp, _ := cid.GetMSPID(ctx.GetStub())

	pubB, _ := ctx.GetStub().GetState("cred:" + credID)
	if pubB == nil {
		return nil, fmt.Errorf("not found")
	}
	var pub CredentialPublic
	_ = json.Unmarshal(pubB, &pub)

	if pub.Status != "Shared" {
		return nil, fmt.Errorf("not shared")
	}
	authorized := false
	for _, m := range pub.SharedWith {
		if m == msp {
			authorized = true
			break
		}
	}
	if !authorized {
		return nil, fmt.Errorf("not authorized for this credential")
	}

	privB, err := ctx.GetStub().GetPrivateData(collection, "credpriv:"+credID)
	if err != nil || privB == nil {
		return nil, fmt.Errorf("no private data accessible")
	}
	var priv CredentialPrivate
	_ = json.Unmarshal(privB, &priv)
	return &priv, nil
}

func main() {
	cc, err := contractapi.NewChaincode(new(Contract))
	if err != nil {
		panic(err)
	}
	if err := cc.Start(); err != nil {
		panic(err)
	}
}
