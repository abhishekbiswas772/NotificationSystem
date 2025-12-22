package helpers

import (
	"encoding/json"
	"fmt"
	"time"
	"github.com/google/uuid"
)

func generateId() string {
	generatedId := uuid.NewString()
	return generatedId
}



func jsonDumps(data map[string]interface{}) (string, error) {
	if data == nil {
		return "", fmt.Errorf("data is nil")
	}
	jsonStr, err := json.Marshal(data)
	if err != nil{
		return "", err
	}
	return string(jsonStr), nil
}

func jsonLoads(data string) (map[string]interface{}, error) {
	if data == "" {
		return nil, fmt.Errorf("empty json string")
	}
	var result map[string]interface{}
	err := json.Unmarshal([]byte(data), &result)
	if err != nil {
		return nil, err
	}
	return result, nil
}


func getTimeStampInSec() int64 {
	now := time.Now()
	nowInSec := now.Unix()
	return nowInSec
}